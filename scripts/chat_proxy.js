#!/usr/bin/env node
// JARVIS Chat Proxy → ROUTEUR LLM UNIFIÉ multi-backend (cascade failover)
// Source de vérité unique = ~/.openclaw/openclaw.json (mêmes providers/clés qu'OpenClaw).
// Exposé 0.0.0.0:18800 → utilisable par TOUT le cluster + pipelines :
//   - /v1/chat/completions + /v1/models  (OpenAI-compat : Claude Code/ccr, Gemini CLI, Lumenflow, agents)
//   - /chat  (legacy {text} : Telegram bots, orchestrateur vocal)
// Cascade : essaie chaque backend dans l'ordre, passe au suivant sur erreur réseau OU réponse vide.

const http = require('http');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const OC_CONFIG = process.env.OPENCLAW_CONFIG || path.join(os.homedir(), '.openclaw/openclaw.json');

// ── Construire la cascade de backends depuis openclaw.json (fallback si illisible) ──
function loadBackends() {
  let providers = {};
  try {
    providers = JSON.parse(fs.readFileSync(OC_CONFIG, 'utf8')).models.providers || {};
  } catch (e) {
    console.error('[proxy] openclaw.json illisible, défauts hardcodés:', e.message);
  }
  const pick = (name) => {
    const p = providers[name];
    if (!p || !p.models || !p.models.length) return null;
    // modelId = modèle par défaut de la cascade ; allModelIds = tout ce que le
    // provider sert et que l'adressage direct `backend/modelId` sait déjà router.
    return { name, baseUrl: p.baseUrl.replace(/\/$/, ''), apiKey: p.apiKey || '', api: p.api, modelId: p.models[0].id, allModelIds: p.models.map(m => m.id) };
  };
  // Ordre = appui local d'abord (câblage 2026-07-16). Override via env BACKEND_ORDER.
  // lmstudio-m1 = qwen/qwen3.5-9b (:1234 DIRECT, 0 réseau, TTFT ~0.1s, flash-attn) = appui prioritaire ;
  // lmstudio-node10 = même modèle relayé (secours) ; ollama/gemma3:4b = fallback rapide ;
  // cloud/m2/gemini = fiabilité. Défaut survit à la race auto-repair.
  const order = (process.env.BACKEND_ORDER || 'lmstudio,lmstudio-m1,lmstudio-node10,ollama,ollama-cloud,lmstudio-m2,gemini').split(',').map(s => s.trim());
  const built = order.map(pick).filter(Boolean);
  // Modèles explicites : rapides/non-vides (évite le budget thinking gaspillé des reasoners)
  for (const b of built) {
    if (b.name === 'ollama') b.modelId = process.env.OLLAMA_MODEL || 'gemma3:4b';
    if (b.name === 'lmstudio-m1' || b.name === 'lmstudio-m2') b.modelId = 'qwen/qwen3.5-9b';
    if (b.name === 'ollama-cloud') b.modelId = 'gpt-oss:120b';
    if (b.name === 'gemini') b.modelId = 'gemini-3.7-flash';
    // Normaliser : OpenAI-compat exige /v1 (ollama local expose /v1/chat/completions ; baseUrl config = :11434 nu)
    if (b.api !== 'google-generative-ai' && !/\/v\d+$/.test(b.baseUrl)) b.baseUrl += '/v1';
  }
  // Filet PERMANENT (2026-08-18) : Ollama local M4 en dernier recours.
  // Cas réel constaté : openclaw.json ne déclarait QUE le provider `lmstudio`
  // (M6 :1234). La cascade construite n'avait alors plus AUCUN repli local —
  // M6 éteint = hub muet. Ce filet ne s'ajoute que s'il manque.
  if (!built.some(b => b.name === 'ollama')) {
    built.push({ name: 'ollama', baseUrl: 'http://127.0.0.1:11434/v1', apiKey: '',
                 api: 'ollama', modelId: process.env.OLLAMA_MODEL || 'gemma3:4b' });
  }
  // Filet de sécurité quand AUCUN nom de BACKEND_ORDER ne correspond à un
  // provider déclaré (cas réel : l'ordre demande lmstudio-m1/node10/ollama
  // alors qu'openclaw.json déclare m1-lmstudio-primary/m4-ollama-gpu/...).
  // Modèle NON-REASONER obligatoire ici : qwen3:1.7b dépensait tout le budget
  // en thinking et rendait content:'' → le proxy traduisait ça en 502.
  // gemma3:4b répond du texte directement, vérifié.
  // Filet à DEUX processus distincts. Avant, il ne contenait qu'Ollama : quand
  // le daemon de bibliothèque saturait Ollama (GPU ~97 %), le hub n'avait plus
  // AUCUN backend — chemin principal et repli partageaient le même point de
  // défaillance. LM Studio est un process séparé, donc un vrai second recours.
  // Le prefill <think></think> ci-dessous s'applique automatiquement à qwen.
  return built.length ? built : [
    { name: 'lmstudio-local', baseUrl: 'http://127.0.0.1:1234/v1', apiKey: '', api: 'openai-completions', modelId: process.env.LMS_MODEL || 'qwen/qwen3.5-9b' },
    { name: 'ollama', baseUrl: 'http://127.0.0.1:11434/v1', apiKey: '', api: 'ollama', modelId: process.env.OLLAMA_MODEL || 'gemma3:4b' },
  ];
}

let BACKENDS = loadBackends();

// ── Défense en profondeur anti-fuite reasoning (2026-07-15) ──
// Le prefill <think></think> couvre qwen/gemma-4. Les autres reasoners (gpt-oss:120b
// via ollama-cloud en fallback) peuvent encore laisser du <think> dans content/reasoning_content.
// stripReasoning retire tout bloc <think>...</think> (multiline, non-greedy) et un <think>
// orphelin non fermé + tout ce qui suit. Après strip, un texte vide => rejet (garde !text.trim()) => backend suivant.
function stripReasoning(text) {
  if (typeof text !== 'string') return '';
  return text
    .replace(/<think\b[^>]*>[\s\S]*?<\/think\s*>/gi, '') // blocs fermés (attributs tolérés), non-greedy
    // Limitation connue : un <think> non fermé légitime dans du contenu tronquerait la suite.
    // Acceptable pour réponses LLM internes où <think> apparaît surtout en erreur ou cas très rares.
    .replace(/<think\b[^>]*>[\s\S]*$/i, '')              // <think> orphelin non fermé => coupe la suite
    .trim();
}

class Semaphore {
  constructor(max) {
    this.max = max;
    this.running = 0;
    this.queue = [];
  }
  // ctx (optionnel) = contexte de requête cliente : si le client part pendant
  // l'attente en file, son entrée est marquée annulée et le slot n'est jamais
  // consommé pour lui (sinon on réservait un slot pour une socket morte).
  acquire(skipIfQueued = false, ctx = null) {
    if (this.running < this.max) {
      this.running++;
      return Promise.resolve(true);
    }
    if (skipIfQueued && this.queue.length >= 1) {
      return Promise.resolve(false);
    }
    return new Promise(resolve => {
      const entry = { resolve, cancelled: false };
      this.queue.push(entry);
      if (ctx) ctx.onAbort(() => {
        if (!entry.cancelled) { entry.cancelled = true; resolve(false); }
      });
    });
  }
  release() {
    this.running--;
    // Les entrées annulées (client parti en file d'attente) sont sautées.
    while (this.queue.length > 0) {
      const entry = this.queue.shift();
      if (entry.cancelled) continue;
      this.running++;
      entry.resolve(true);
      return;
    }
  }
}

const semaphores = {};
function getSemaphore(backendName) {
  if (!semaphores[backendName]) {
    let limit = 999;
    if (backendName.startsWith('lmstudio')) {
      limit = 1; // Limite stricte à 1 requête simultanée pour LM Studio afin de ne pas engorger le GPU
    } else if (backendName === 'ollama' || backendName === 'rem-linux' || backendName.startsWith('m6')) {
      // Ollama local et rem-linux servent l'inférence en CPU : 2 requêtes max.
      // rem-linux héberge aussi le Leader Swarm de production, la limite par
      // défaut (999) y noierait 8 cœurs déjà chargés.
      // 2026-08-04 : m6-* (câble direct 10.42.0.230) = 4 cœurs / 11 Go, déjà à
      // load 6 avec ollama à 300 % CPU. Même borne, sinon on refait rem-linux.
      limit = 2;
    }
    semaphores[backendName] = new Semaphore(limit);
  }
  return semaphores[backendName];
}

// ── Identité de requête pour l'instrumentation (2026-08-01) ──
// phash = empreinte courte du dernier message user → permet de mesurer les doublons
// (91 % de titres dupliqués côté producteur, invisibles jusqu'ici dans le log).
function shortHash(s) { return crypto.createHash('sha1').update(String(s)).digest('hex').slice(0, 8); }
function promptHash(messages) {
  try {
    const list = Array.isArray(messages) ? messages : [];
    const last = [...list].reverse().find(m => m && m.role === 'user') || list[list.length - 1] || {};
    const c = last.content;
    return shortHash(typeof c === 'string' ? c : JSON.stringify(c || ''));
  } catch (_) { return 'nohash'; }
}
function clientTag(req) {
  const ua = req.headers && req.headers['user-agent'];
  if (ua) return String(ua).slice(0, 40);
  return 'port:' + ((req.socket && req.socket.remotePort) || '?');
}

// ── Contexte de requête cliente : porte l'abandon (2026-08-01) ──
// Sans lui, un client parti au timeout 90 s laissait le backend générer jusqu'au bout
// en gardant le slot du sémaphore (mesuré : 14,6 h de génération/24 h pour personne).
function makeCtx(req) {
  const handlers = new Set();
  const ctx = {
    aborted: false,
    client: clientTag(req),
    via: null,
    phash: null,
    onAbort(fn) {
      if (ctx.aborted) { try { fn(); } catch (_) {} return () => {}; }
      handlers.add(fn);
      return () => handlers.delete(fn);
    },
    abort() {
      if (ctx.aborted) return;
      ctx.aborted = true;
      for (const fn of [...handlers]) { try { fn(); } catch (_) {} }
      handlers.clear();
    },
  };
  return ctx;
}

// ── Appel d'un backend (OpenAI chat/completions ou Gemini). Résout {text} ou rejette. ──
function callBackend(b, messages, maxTokens, ctx) {
  return new Promise(async (resolve, reject) => {
    const tStart = Date.now();
    if (ctx && ctx.aborted) {
      const gone = new Error(`${b.name}: client parti avant l'appel`);
      gone.clientGone = true;
      return reject(gone);
    }
    const sem = getSemaphore(b.name);
    // Si la file d'attente a déjà une requête en attente, on rejette immédiatement pour failover cascade
    const acquired = await sem.acquire(true, ctx);
    if (!acquired) {
      if (ctx && ctx.aborted) {
        logCascade({ ts: new Date().toISOString(), via: ctx.via || 'chat', event: 'client_gone',
          backend: b.name, stage: 'queue', ms: Date.now() - tStart, ok: false, phash: ctx.phash, client: ctx.client });
        const gone = new Error(`${b.name}: client parti (en file)`);
        gone.clientGone = true;
        return reject(gone);
      }
      const busy = new Error(`${b.name} surcharge (file d'attente active)`);
      busy.overload = true; // distingue la surcharge (→429) d'une panne réelle (→502)
      return reject(busy);
    }

    let r = null;
    let offAbort = null;
    let released = false;
    const release = () => {
      if (offAbort) { offAbort(); offAbort = null; }
      if (!released) {
        released = true;
        sem.release();
      }
    };

    // Client parti pendant la génération : on tue la requête sortante et on rend le slot
    // immédiatement. Le garde `released` rend release() idempotent.
    offAbort = ctx ? ctx.onAbort(() => {
      try { if (r) r.destroy(); } catch (_) {}
      release();
      logCascade({ ts: new Date().toISOString(), via: ctx.via || 'chat', event: 'client_gone',
        backend: b.name, stage: 'inflight', ms: Date.now() - tStart, ok: false, phash: ctx.phash, client: ctx.client });
      const gone = new Error(`${b.name}: client parti`);
      gone.clientGone = true;
      reject(gone);
    }) : null;

    let urlStr, payload, headers = { 'Content-Type': 'application/json' };
    if (b.api === 'google-generative-ai') {
      // Gemini REST : génération via :generateContent
      urlStr = `${b.baseUrl}/models/${b.modelId}:generateContent?key=${b.apiKey}`;
      const contents = messages.map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] }));
      payload = JSON.stringify({ contents, generationConfig: { maxOutputTokens: maxTokens } });
    } else {
      urlStr = `${b.baseUrl}/chat/completions`;
      if (b.apiKey) headers['Authorization'] = `Bearer ${b.apiKey}`;
      // Anti reasoning-runaway (2026-07-15) : qwen/gemma-4 sous LM Studio raisonnent sans fin
      // (content vide + ~700 tokens gaspillés + fuite reasoning_content si max_tokens petit).
      // Prefill assistant <think></think> fermé => réponse directe ~2s, pas de fuite. Clone (messages partagé cascade).
      const needsPrefill = /qwen|gemma-4/i.test(b.modelId);
      const msgs = needsPrefill ? [...messages, { role: 'assistant', content: '<think>\n\n</think>\n\n' }] : messages;
      payload = JSON.stringify({ model: b.modelId, messages: msgs, max_tokens: maxTokens, stream: false });
    }
    const url = new URL(urlStr);
    const lib = url.protocol === 'https:' ? https : http;
    const opts = { hostname: url.hostname, port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname + url.search, method: 'POST', headers, timeout: 90000 };
    headers['Content-Length'] = Buffer.byteLength(payload);
    r = lib.request(opts, (resp) => {
      let data = '';
      resp.on('data', d => data += d);
      resp.on('end', () => {
        release();
        try {
          const j = JSON.parse(data);
          let text;
          if (b.api === 'google-generative-ai') {
            text = j.candidates?.[0]?.content?.parts?.map(p => p.text).join('') || '';
          } else {
            const msg = j.choices?.[0]?.message || {};
            // Défense en profondeur : strip <think> sur content ET sur le fallback reasoning_content.
            // Si tout est reasoning => text vide => rejet (garde !text.trim()) => backend suivant.
            text = stripReasoning(msg.content) || stripReasoning(msg.reasoning_content);
          }
          if (resp.statusCode >= 400 || !text || !text.trim()) return reject(new Error(`${b.name} vide/HTTP${resp.statusCode}`));
          resolve({ text, model: `${b.name}/${b.modelId}` });
        } catch (e) { reject(new Error(`${b.name} parse: ${e.message}`)); }
      });
    });
    r.on('error', e => { release(); reject(new Error(`${b.name}: ${e.message}`)); });
    r.on('timeout', () => { r.destroy(); release(); reject(new Error(`${b.name}: timeout`)); });
    r.write(payload); r.end();
  });
}


// ── Log local de la cascade domino (best-effort, non bloquant, jamais d'erreur) ──
const LOG_PATH = process.env.CASCADE_LOG || path.join(os.homedir(), 'jarvis/data/llm_cascade_log.jsonl');
function logCascade(entry) { try { fs.appendFile(LOG_PATH, JSON.stringify(entry) + '\n', () => {}); } catch (_) {} }

// ── Lanes de qualité : réordonnent la cascade selon le champ `model` du client. ──
// Pure : part de BACKENDS (cascade complète), met en tête le backend ciblé (cloné),
// garde les autres derrière en fallback. jarvis-auto/inconnu/absent → BACKENDS inchangé.
function laneBackends(model) {
  // Map lane → {backend name à mettre en tête, modelId optionnel à forcer}
  let spec = ({
    'jarvis-fast':    { backend: 'ollama' },
    'jarvis-quality': { backend: 'ollama-cloud' },
    'jarvis-code':    { backend: 'ollama-cloud', modelId: 'qwen3-coder:480b' },
  })[model];
  // Adressage direct `backend/modelId` — c'est le format que /v1/models publie
  // lui-même plus bas. Sans ce parse, demander « rem-linux/gemma3:4b » était
  // silencieusement servi par lmstudio-m1 : le hub annonçait des modèles qu'il ne
  // savait pas router. Le modelId peut contenir « / » et « : » (ex.
  // « lmstudio-m1/qwen/qwen3.5-9b ») → on coupe au 1er « / », et seulement si le
  // préfixe correspond à un backend réellement déclaré.
  if (!spec && typeof model === 'string' && model.includes('/')) {
    const cut = model.indexOf('/');
    const prefix = model.slice(0, cut);
    const rest = model.slice(cut + 1);
    if (rest && BACKENDS.some(b => b.name === prefix)) spec = { backend: prefix, modelId: rest };
  }
  if (!spec) return BACKENDS; // jarvis-auto / inconnu / absent → cascade complète inchangée
  const head = BACKENDS.find(b => b.name === spec.backend);
  if (!head) return BACKENDS; // backend ciblé absent → cascade complète (sûr)
  const clone = { ...head };
  if (spec.modelId) clone.modelId = spec.modelId;
  const rest = BACKENDS.filter(b => b !== head);
  return [clone, ...rest];
}

// ── Cascade : premier backend qui répond non-vide gagne. Logue la décision en local. ──
async function route(messages, maxTokens, via, model, ctx) {
  const errs = [];
  const t0 = Date.now();
  const phash = promptHash(messages);
  const client = ctx ? ctx.client : 'inconnu';
  if (ctx) { ctx.via = via || 'chat'; ctx.phash = phash; }
  // overloadOnly : vrai tant qu'AUCUN backend n'a été réellement essayé (tous
  // refusés en amont pour surcharge) → réponse 429, pas 502.
  let overloadOnly = true;
  for (const b of laneBackends(model)) {
    if (ctx && ctx.aborted) break;
    try {
      const r = await callBackend(b, messages, maxTokens, ctx);
      logCascade({ ts: new Date().toISOString(), via: via || 'chat', backend: b.name, served: r.model, ms: Date.now() - t0, ok: true, tried: errs.length, chars: (r.text || '').length, phash, client });
      return r;
    } catch (e) {
      if (e.clientGone) throw e; // socket morte : inutile de descendre la cascade
      errs.push(`${b.name}:${e.message}`);
      if (!e.overload) overloadOnly = false;
    }
  }
  if (ctx && ctx.aborted) {
    const gone = new Error('client parti');
    gone.clientGone = true;
    throw gone;
  }
  logCascade({ ts: new Date().toISOString(), via: via || 'chat', served: null, ms: Date.now() - t0, ok: false, tried: errs.length, errs, phash, client, overloaded: overloadOnly && errs.length > 0 });
  const err = new Error('tous backends KO: ' + errs.join(' | '));
  if (overloadOnly && errs.length > 0) err.overloaded = true;
  throw err;
}

// Réponse commune aux deux familles de routes : 429 si surcharge pure, 502 si panne réelle,
// silence si le client est déjà parti (écrire sur une socket morte ne sert à rien).
function respondError(res, ctx, e, extra) {
  if (e.clientGone || res.writableEnded || (ctx && ctx.aborted)) return;
  if (e.overloaded) {
    res.writeHead(429, { 'Content-Type': 'application/json', 'Retry-After': '20' });
    res.end(JSON.stringify({ error: 'surcharge: tous les backends sont occupés',
      code: 'backends_busy', detail: e.message, retry_after: 20,
      text: 'Hub LLM saturé, aucun backend libre. Réessayer dans 20 s.' }));
    return;
  }
  res.writeHead(502, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(Object.assign({ error: e.message }, extra || {})));
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  if (req.url === '/health' || req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', proxy: 'JARVIS-unified-router', cascade: BACKENDS.map(b => b.name) }));
    return;
  }

  // OpenAI : liste de modèles (le hub expose un modèle logique "jarvis-auto" + chaque backend)
  if (req.url === '/v1/models' && req.method === 'GET') {
    const models = [
      { id: 'jarvis-auto', object: 'model', owned_by: 'jarvis' },
      { id: 'jarvis-fast', object: 'model', owned_by: 'jarvis' },
      { id: 'jarvis-quality', object: 'model', owned_by: 'jarvis' },
      { id: 'jarvis-code', object: 'model', owned_by: 'jarvis' },
    // Un backend peut servir plusieurs modèles chargés en parallèle (LM Studio
    // M1 : qwen + hermes). Ne publier que b.modelId revenait à cacher des
    // modèles que l'adressage direct savait pourtant router. Le défaut de
    // cascade reste en tête de liste pour les clients qui prennent le premier.
    ].concat(BACKENDS.flatMap(b => {
      const ids = Array.from(new Set([b.modelId, ...(b.allModelIds || [])]));
      return ids.map(id => ({ id: `${b.name}/${id}`, object: 'model', owned_by: b.name }));
    }));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ object: 'list', data: models }));
    return;
  }

  if ((req.url === '/chat' || req.url === '/v1/chat/completions') && req.method === 'POST') {
    let body = '';
    const ctx = makeCtx(req);
    // 'close' est aussi émis à la fin normale : le garde writableEnded distingue
    // « réponse déjà partie » de « client parti avant la réponse ».
    // req 'close' est émis dès que le body est entièrement lu : ce n'est un abandon
    // que si la requête est incomplète (req.complete faux). res 'close' avant
    // writableEnded = le client a coupé pendant la génération : c'est le cas mesuré.
    req.on('close', () => { if (!req.complete) ctx.abort(); });
    res.on('close', () => { if (!res.writableEnded) ctx.abort(); });
    req.on('data', d => body += d);
    req.on('end', async () => {
      let payload;
      try { payload = JSON.parse(body); } catch (e) { payload = { messages: [{ role: 'user', content: body }] }; }
      const messages = payload.messages || [{ role: 'user', content: payload.text || payload.content || body }];
      const maxTokens = payload.max_tokens || 4096;  // reasoning models : >2k sinon content vide
      const openaiFmt = req.url === '/v1/chat/completions';
      try {
        const { text, model } = await route(messages, maxTokens, openaiFmt ? 'v1/chat' : 'chat', payload.model, ctx);
        if (ctx.aborted || res.writableEnded) return;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        if (openaiFmt) {
          res.end(JSON.stringify({ id: 'chatcmpl-jarvis', object: 'chat.completion', model,
            choices: [{ index: 0, message: { role: 'assistant', content: text }, finish_reason: 'stop' }] }));
        } else {
          res.end(JSON.stringify({ text, model }));
        }
      } catch (e) {
        respondError(res, ctx, e, { text: 'LLM indisponible (cascade épuisée)' });
      }
    });
    return;
  }

  // OpenAI legacy /v1/completions (texte) — pour le board (prompt ChatML → messages).
  if (req.url === '/v1/completions' && req.method === 'POST') {
    let body = '';
    const ctx = makeCtx(req);
    req.on('close', () => { if (!req.complete) ctx.abort(); });
    res.on('close', () => { if (!res.writableEnded) ctx.abort(); });
    req.on('data', d => body += d);
    req.on('end', async () => {
      let payload; try { payload = JSON.parse(body); } catch (e) { payload = { prompt: body }; }
      const raw = payload.prompt || payload.text || '';
      // Parse ChatML si présent, sinon prompt = un seul tour user.
      let messages;
      const sysM = raw.match(/<\|im_start\|>system\n([\s\S]*?)<\|im_end\|>/);
      const usrM = raw.match(/<\|im_start\|>user\n([\s\S]*?)<\|im_end\|>/);
      if (usrM) {
        messages = [];
        if (sysM) messages.push({ role: 'system', content: sysM[1] });
        messages.push({ role: 'user', content: usrM[1] });
      } else {
        messages = [{ role: 'user', content: raw }];
      }
      const maxTokens = payload.max_tokens || 700;
      try {
        const { text, model } = await route(messages, maxTokens, 'v1/chat', payload.model, ctx);
        if (ctx.aborted || res.writableEnded) return;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ id: 'cmpl-jarvis', object: 'text_completion', model,
          choices: [{ index: 0, text, finish_reason: 'stop' }] }));
      } catch (e) {
        respondError(res, ctx, e, { choices: [{ text: '', finish_reason: 'error' }] });
      }
    });
    return;
  }

  // Ollama natif : /api/chat → {message:{content}} ; /api/generate → {response}
  if ((req.url === '/api/chat' || req.url === '/api/generate') && req.method === 'POST') {
    let body = '';
    const ctx = makeCtx(req);
    // req 'close' est émis dès que le body est entièrement lu : ce n'est un abandon
    // que si la requête est incomplète (req.complete faux). res 'close' avant
    // writableEnded = le client a coupé pendant la génération : c'est le cas mesuré.
    req.on('close', () => { if (!req.complete) ctx.abort(); });
    res.on('close', () => { if (!res.writableEnded) ctx.abort(); });
    req.on('data', d => body += d);
    req.on('end', async () => {
      let p; try { p = JSON.parse(body); } catch (e) { p = {}; }
      const isGen = req.url === '/api/generate';
      const messages = p.messages || [{ role: 'user', content: p.prompt || p.text || body }];
      try {
        const { text, model } = await route(messages, p.max_tokens || (p.options && p.options.num_predict) || 4096, isGen ? 'api/generate' : 'api/chat', p.model, ctx);
        if (ctx.aborted || res.writableEnded) return;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        const base = { model, created_at: new Date().toISOString(), done: true, done_reason: 'stop' };
        res.end(JSON.stringify(isGen ? { ...base, response: text } : { ...base, message: { role: 'assistant', content: text } }));
      } catch (e) {
        respondError(res, ctx, e);
      }
    });
    return;
  }

  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ status: 'JARVIS Unified Router', routes: ['/v1/chat/completions', '/v1/models', '/api/chat', '/api/generate', '/chat', '/health'] }));
});

// Recharge la cascade à chaud sur SIGHUP (après édition openclaw.json)
process.on('SIGHUP', () => { BACKENDS = loadBackends(); console.log('[proxy] cascade rechargée:', BACKENDS.map(b => b.name).join(' → ')); });

const LISTEN_PORT = process.env.PORT || 18800;

// Démarrer le serveur uniquement en exécution directe (pas lors d'un require() de test).
if (require.main === module) {
  console.log('[proxy] cascade:', BACKENDS.map(b => `${b.name}/${b.modelId}`).join(' → '));
  server.listen(LISTEN_PORT, '0.0.0.0', () => console.log('JARVIS Unified Router on 0.0.0.0:' + LISTEN_PORT));
}

// Exports pour tests unitaires isolés (n'ouvre aucun port).
module.exports = { stripReasoning, callBackend, loadBackends, getSemaphore };
