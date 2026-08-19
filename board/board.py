#!/usr/bin/env python3
"""board — conseil d'experts local et souverain. 0 token payant.

Une question entre. N experts du domaine repondent, chacun avec SA grille de
lecture, chacun EN CITANT le corpus indexe. Un arbitre tranche les desaccords.
Ce n'est pas un chatbot : **une reponse sans citation est rejetee**, et la regle
est verifiable en SQL (vue `answers_sans_citation`), pas seulement demandee.

Stockage : SQLite + FTS5, embeddings BLOB float32 dim 768 (constatee en phase 0).
Inference et vectorisation : LM Studio 127.0.0.1:1234, local. Rien ne sort.

    board.py init
    board.py domain add <id> "<nom>" ["<description>"]
    board.py expert add <id> <domain> "<nom>" "<lens>" [--arbitre]
    board.py ingest <domain> <chemin|glob> [--expert ID] [--kind md]
    board.py embed [--limit N]
    board.py ask <domain> "<question>" [--k 6] [--experts a,b]
    board.py status
"""

from __future__ import annotations

import glob as globmod
import hashlib
import json
import os
import random
import re
import socket
import sqlite3
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "board.db"
SCHEMA = ROOT / "board_schema.sql"

# Configurables : le board vient de M1, où qwen3.5-9b se chargeait. Sur une
# machine à 4 Go de VRAM il échoue en cudaMalloc OOM (compute buffers), alors
# que qwen2.5-coder-14b se charge. Un modèle codé en dur rend le board
# inutilisable ailleurs que sur sa machine d'origine.
# 2026-08-18 — le defaut visait 127.0.0.1:1234, herite de M1 ou LM Studio
# tournait en local. Sur M4 rien n'ecoute sur ce port : LM Studio est sur M6
# (cable direct, RTT ~1.4 ms). Sans override explicite, embed et ask tombaient
# tous les deux sur un backend mort. Override toujours possible via $BOARD_LMS_URL.
LMS = os.environ.get("BOARD_LMS_URL", "http://10.42.0.230:1234/v1")
# Endpoint d'INFÉRENCE, distinct de celui des embeddings. Sur un GPU de 4 Go,
# LM Studio ne tient qu'un modèle : dès que le modèle d'embedding est chargé,
# toute demande de chat échoue en « Failed to load model ». Séparer les deux
# backends (embeddings ici, chat ailleurs) est la seule façon de faire tourner
# le board sur cette machine. Ollama expose une API OpenAI-compatible sur /v1.
CHAT_URL = os.environ.get("BOARD_CHAT_URL", LMS)
EMBED_MODEL = os.environ.get(
    "BOARD_EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5"
)
EMBED_DIM = 768  # CONSTATEE, pas supposee (3 appels concordants)
# Defaut mesure 2026-08-14 sur M6 (RTX 2060, 12 Go) : qwen2.5-coder-14b y meurt
# au chargement (« Engine protocol startup was aborted »), et comme les 48
# experts ont `model` NULL ils retombaient TOUS dessus — le board rendait
# « aucun expert n'a repondu » sur chaque question. qwen3.5-9b se charge et
# tient 16k de contexte sur cette carte.
CHAT_MODEL = os.environ.get("BOARD_CHAT_MODEL", "qwen/qwen3.5-9b")


def modele_de(e) -> str:
    """Modele affecte a un expert, CHAT_MODEL a defaut.

    La colonne experts.model est optionnelle et peut valoir NULL : un expert sans
    affectation retombe sur le modele par defaut, exactement comme dans chat().

    BOARD_FORCE_MODEL=1 ignore l'affectation par expert. Necessaire des qu'on
    change de BACKEND : les noms stockes en base sont ceux du parc local
    (qwen3:1.7b, hermes-2-pro…) et n'existent pas chez un fournisseur cloud —
    sans ce forcage, les experts ainsi affectes partent en panne backend un a un
    pendant que les autres repondent, ce qui donne une table ronde amputee sans
    que rien ne le signale.
    """
    if os.environ.get("BOARD_FORCE_MODEL", "").strip() in ("1", "true", "oui"):
        return CHAT_MODEL
    try:
        return e["model"] or CHAT_MODEL
    except (IndexError, KeyError):
        return CHAT_MODEL


CHUNK_CHARS, CHUNK_OVERLAP = 1400, 200
# Deux des cinq GPU n'ont plus de ventilateur : ils montent a 86-88 sous
# charge, l'arret materiel est a 96. On s'arrete AVANT la zone rouge.
GPU_TEMP_MAX = 89


# ─────────────────────────────────────────────────────────── base
def con() -> sqlite3.Connection:
    c = sqlite3.connect(DB, timeout=60)
    # PRAGMA foreign_keys est PAR CONNEXION : le declarer dans le schema ne
    # persiste rien. Sans cette ligne, supprimer un domaine laisse ses chunks
    # orphelins en silence — constate au premier test.
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA busy_timeout = 60000")
    c.row_factory = sqlite3.Row
    return c


def to_blob(v: list[float]) -> bytes:
    return struct.pack(f"{len(v)}f", *v)


def from_blob(b: bytes) -> list[float]:
    return list(struct.unpack(f"{len(b) // 4}f", b))


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):  # dimensions differentes = refus,
        return -1.0  # jamais un score silencieusement faux
    d = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return d / (na * nb) if na and nb else 0.0


# ─────────────────────────────────────────────────────────── LM Studio
def _post(path: str, payload: dict, timeout: int = 180) -> dict:
    base = LMS if path.startswith("/embeddings") else CHAT_URL
    headers = {"Content-Type": "application/json"}
    # LM Studio local n'exige pas d'authentification, mais un backend
    # OpenAI-compatible distant (Ollama Cloud, z.ai…) refuse sans jeton. La clé
    # reste hors du code : coffre sops -> variable d'environnement.
    key = os.environ.get("BOARD_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(
        f"{base}{path}",
        data=json.dumps(payload).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


class Embedding(list):
    """Vecteur d'embedding QUI PORTE SA CAUSE D'ECHEC.

    Sous-classe de `list` pour une raison precise : un echec doit rester
    *falsy* et se comporter exactement comme l'ancien `None` pour tout code
    qui ecrit `if v:` — mais sans perdre l'information. Un `None` muet a
    rendu 19 echecs sur 250 indistinguables : timeout ? HTTP 500 ? dimension
    inattendue ? On ne pouvait pas decider quoi faire.

    Succes -> EMBED_DIM flottants, `cause` a None.
    Echec  -> liste vide (falsy), `cause` renseignee : "timeout", "reseau",
    "http_<code>", "reponse_illisible", "dimension".
    """

    __slots__ = ("cause", "detail")

    def __init__(self, vec=(), cause=None, detail=""):
        super().__init__(vec)
        self.cause = cause
        self.detail = detail


def embed_lot(texts: list, role: str = "document") -> list:
    """Vectorise un LOT de textes en un seul appel API (input = liste).

    Un aller-retour reseau pour N textes au lieu de N : c'est le levier de
    debit principal quand le backend est distant (latence > temps GPU).
    Si le backend refuse la forme liste ou repond incomplet, on retombe
    texte par texte via embed() — aucun chunk n'est perdu, juste plus lent.
    """
    prefixe = "search_query: " if role == "query" else "search_document: "
    try:
        d = _post(
            "/embeddings",
            {"model": EMBED_MODEL, "input": [prefixe + t[:8000] for t in texts]},
        )
        data = d["data"]
        if len(data) == len(texts):
            data = sorted(data, key=lambda x: x.get("index", 0))
            vs = []
            for item in data:
                v = item["embedding"]
                vs.append(
                    Embedding(v)
                    if len(v) == EMBED_DIM
                    else Embedding(cause="dimension", detail=f"{len(v)} != {EMBED_DIM}")
                )
            return vs
    except Exception:
        pass  # repli unitaire ci-dessous, qui remonte les causes une a une
    return [embed(t, role=role) for t in texts]


def embed(text: str, tentatives: int = 2, role: str = "document") -> Embedding:
    """Vectorise un texte et REMONTE la cause en cas d'echec.

    Une seule tentative supplementaire, et seulement pour ce qui est
    transitoire : timeout, panne reseau, HTTP 5xx. Une dimension fausse ou
    un HTTP 4xx se reproduiront a l'identique — les reessayer ne fait que
    doubler le temps perdu, on rend la main tout de suite.

    R3-rag — le PREFIXE n'est pas cosmetique. nomic-embed-text declare deux
    prefixes obligatoires : `search_query:` pour ce qu'on cherche,
    `search_document:` pour ce qu'on indexe. Le modele projette les deux dans
    des sous-espaces volontairement distincts ; sans prefixe, requete et
    fragment tombent au meme endroit et la similarite mesure autre chose que
    ce qu'on croit. Les 9 278 vecteurs calcules sans prefixe etaient donc hors
    specification — d'ou leur invalidation.

    Le prefixe est pose AVANT le tronquage : sinon un texte de 8 000
    caracteres perdrait ses derniers octets pour loger l'etiquette.
    """
    prefixe = "search_query: " if role == "query" else "search_document: "
    dernier = Embedding(cause="inconnu")
    for essai in range(max(1, tentatives)):
        try:
            d = _post(
                "/embeddings", {"model": EMBED_MODEL, "input": prefixe + text[:8000]}
            )
        except urllib.error.HTTPError as e:
            if e.code == 404 and "text-embedding" in EMBED_MODEL:
                try:
                    d = _post(
                        "/embeddings", {"model": "nomic-embed-text:latest", "input": prefixe + text[:8000]}
                    )
                except Exception:
                    dernier = Embedding(cause=f"http_{e.code}", detail=str(e.reason))
                else:
                    v = d["data"][0]["embedding"]
                    if len(v) == EMBED_DIM:
                        return Embedding(v)
            else:
                dernier = Embedding(cause=f"http_{e.code}", detail=str(e.reason))
        except (socket.timeout, TimeoutError) as e:
            dernier = Embedding(cause="timeout", detail=str(e) or "delai depasse")
        except urllib.error.URLError as e:
            # URLError enveloppe le timeout socket : sans ce demelage, un
            # delai depasse serait compte comme une panne reseau.
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                dernier = Embedding(cause="timeout", detail=str(e.reason))
            else:
                dernier = Embedding(cause="reseau", detail=str(e.reason))
        except ValueError as e:  # json.JSONDecodeError en herite
            return Embedding(cause="reponse_illisible", detail=f"{type(e).__name__}")
        except Exception as e:
            dernier = Embedding(cause="reseau", detail=f"{type(e).__name__}: {e}")
        else:
            try:
                v = d["data"][0]["embedding"]
            except (KeyError, IndexError, TypeError) as e:
                return Embedding(
                    cause="reponse_illisible", detail=f"{type(e).__name__}: {e}"
                )
            if len(v) != EMBED_DIM:
                return Embedding(cause="dimension", detail=f"{len(v)} != {EMBED_DIM}")
            return Embedding(v)
        c = dernier.cause
        transitoire = c in ("timeout", "reseau") or (
            c.startswith("http_") and c[5:].isdigit() and int(c[5:]) >= 500
        )
        if not transitoire or essai + 1 >= max(1, tentatives):
            break
        time.sleep(1.5)  # laisser le backend respirer avant le second essai
    return dernier


def gpu_temp_max() -> int | None:
    """Temperature GPU la plus elevee, ou None si la mesure est indisponible.

    Fail-safe volontaire : pas de nvidia-smi, sortie illisible ou commande
    qui traine = None. L'ABSENCE de mesure ne doit jamais bloquer un
    traitement ; seule une mesure REELLE au-dessus du seuil l'arrete.
    """
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        temps = [int(x.strip()) for x in out.stdout.splitlines() if x.strip().isdigit()]
        return max(temps) if temps else None
    except Exception:
        return None


def chat(
    system: str,
    user: str,
    max_tokens: int | None = None,
    model: str | None = None,
) -> tuple[str, int]:
    """Appel qwen3.5 SANS reasoning-runaway.

    Un prefixe « /nothink » sur /chat/completions NE SUFFIT PAS : le modele
    raisonne jusqu'a epuiser max_tokens et rend un `content` VIDE — constate
    ici meme, 4 experts, 4 reponses vides, 40 a 72 s chacune. Le seul remede
    eprouve passe par /v1/completions avec un prompt ChatML brut ou le bloc
    <think></think> est DEJA FERME dans le tour de l'assistant : le modele n'a
    plus d'endroit ou raisonner, il ecrit directement sa reponse.
    """
    t0 = time.time()
    # Budget de sortie. 700 suffit a un modele qui repond directement, mais un
    # modele a raisonnement (gpt-oss:120b) le consomme ENTIEREMENT en reflexion
    # et rend un `content` vide : mesure 2026-08-14, une reponse simple sortait
    # a 691 caracteres pour un plafond de 700, c'est-a-dire au ras de la limite.
    if max_tokens is None:
        max_tokens = int(os.environ.get("BOARD_MAX_TOKENS", "700"))
    # Fenetres de contexte par modele (tokens, lues sur `lms ps`). Diagnostic
    # 2026-08-08 : les prompts du board (extraits k=6) depassent les 4096 tokens
    # d'hermes -> HTTP 400 exceed_context_size systematique -> les 17 experts
    # hermes ne deliberaient JAMAIS et la cascade rendait le board mono-qwen.
    # On tronque le MILIEU du tour user (les extraits), jamais la question ni
    # la consigne, pour tenir dans fenetre - max_tokens - marge ChatML.
    # ROOT CAUSE mesuree 2026-08-08 (test 2 requetes concurrentes) : le ctx du
    # modele est un POOL PARTAGE entre requetes paralleles — 4096 chez hermes
    # devient ~2048/requete des que 2 experts tirent ensemble, et la generation
    # meurt en plein stream ("Context size has been exceeded" a ~80 s). Les
    # budgets ci-dessous sont donc les fenetres EFFECTIVES sous concurrence
    # (ctx_total / 2), pas les fenetres affichees par `lms ps`.
    CTX_TOKENS = {
        "hermes-2-pro-mistral-7b": 2048,
        # M6 charge qwen3.5-9b a 16384 avec --parallel 4. Le ctx etant un pool
        # partage entre requetes concurrentes, la fenetre EFFECTIVE par expert
        # est 16384/4 = 4096 ; on retient 8192, valeur tenable a 2 experts
        # simultanes, et la troncature du milieu couvre le reste.
        "qwen/qwen3.5-9b": 8192,
        "deepseek/deepseek-r1-0528-qwen3-8b": 4096,
        "qwen/qwen2.5-coder-14b": 4096,
    }
    ctx = CTX_TOKENS.get(model or CHAT_MODEL)
    if ctx:
        # 2.5 car/token : mesure prudente pour du francais en ChatML. La v1 a
        # 3 car/token laissait encore deborder (~4300 tokens > 4096) et hermes
        # restait « injoignable » malgre la troncature.
        budget_chars = int((ctx - max_tokens - 200) * 2.5)
        if len(system) + len(user) > budget_chars:
            garde = max(1000, (budget_chars - len(system)) // 2)
            user = (
                user[:garde]
                + "\n[... extraits tronques : fenetre de contexte du modele ...]\n"
                + user[-garde:]
            )
    # Le prompt ChatML brut ci-dessus suppose /v1/completions, que LM Studio et
    # Ollama exposent. Un backend cloud OpenAI-compatible (Mistral) ne sert QUE
    # /v1/chat/completions et repond HTTP 422 « messages: Field required » sur
    # l'autre route — constate 2026-08-17, 4 experts en panne backend d'un coup.
    # BOARD_CHAT_API=chat bascule sur la route messages ; le defaut reste
    # « completions » pour ne rien changer au chemin local eprouve (l'astuce du
    # <think></think> deja ferme n'y a pas d'equivalent, mais les modeles cloud
    # ne souffrent pas du reasoning-runaway qu'elle contourne).
    api = os.environ.get("BOARD_CHAT_API", "completions").strip().lower()
    if api == "chat":
        msgs = [{"role": "system", "content": system}] if system.strip() else []
        msgs.append({"role": "user", "content": user})
        payload_chat = {
            "model": model or CHAT_MODEL,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
    p = f"<|im_start|>system\n{system}<|im_end|>\n" if system.strip() else ""
    p += f"<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    try:
        d = _post(
            "/chat/completions" if api == "chat" else "/completions",
            payload_chat
            if api == "chat"
            else {
                "model": model or CHAT_MODEL,
                "prompt": p,
                "max_tokens": max_tokens,
                "stop": ["<|im_end|>"],
                "temperature": 0.3,
            },
            # Les experts ne tournent pas tous sur le meme modele et les debits
            # varient du simple au double : mesure a 4 requetes simultanees,
            # hermes-7b rend 300 jetons en 70 s la ou qwen-9b en met 25. A
            # max_tokens=700 le defaut de 180 s coupait systematiquement les
            # experts du modele lent — ils n'ont JAMAIS delibere, en silence,
            # et seul le modele rapide votait.
            timeout=360,
        )
        ch = d["choices"][0]
        # /completions rend `text`, /chat/completions rend `message.content` :
        # lire la mauvaise cle rendait une reponse VIDE sans lever d'erreur,
        # donc un expert « muet » indiscernable d'un expert sans avis.
        txt = (
            (ch.get("message") or {}).get("content")
            if api == "chat"
            else ch.get("text")
        ) or ""
        txt = txt.strip()
    except urllib.error.HTTPError as e:
        # Le CODE et le CORPS portent la cause reelle (modele decharge en cours
        # de route, file pleine, prompt trop long). N'en garder que le nom de
        # classe rendait la panne indiagnosticable : « HTTPError » ne dit pas
        # s'il faut recharger un modele, attendre, ou raccourcir le prompt.
        try:
            corps = e.read().decode("utf-8", "replace").strip()[:200]
        except Exception:
            corps = ""
        txt = f"[echec backend: HTTP {e.code}{' ' + corps if corps else ''}]"
    except Exception as e:
        txt = f"[echec backend: {type(e).__name__}]"
    return txt or "[reponse vide]", int((time.time() - t0) * 1000)


# ─────────────────────────────────────────────────────────── ingestion
def chunk_text(t: str) -> list[str]:
    t = re.sub(r"\n{3,}", "\n\n", t.strip())
    out, i = [], 0
    while i < len(t):
        j = min(i + CHUNK_CHARS, len(t))
        if j < len(t):  # couper sur une frontiere lisible
            for sep in ("\n\n", "\n", ". "):
                k = t.rfind(sep, i + CHUNK_CHARS // 2, j)
                if k > 0:
                    j = k + len(sep)
                    break
        out.append(t[i:j].strip())
        # Deux pieges successifs a cet endroit, tous deux mesures :
        #  1. `max(..., j)` annulait TOUT recouvrement (j-200 < j donc i=j).
        #     Recouvrement reel : 0 au lieu de 200.
        #  2. `max(..., i+1)` corrigeait (1) mais faisait BOUCLER la queue :
        #     au dernier tour j == len(t), donc j-200 < i, donc i avance de
        #     1 caractere et on reemet une queue quasi identique a chaque
        #     iteration. Mesure sur un fichier de 3 162 caracteres :
        #     123 chunks au lieu de 3, dont 120 doublons de 200 a 81 octets.
        # Le texte est epuise des que j atteint sa fin : c'est la vraie
        # condition d'arret, et elle doit primer sur toute progression.
        if j >= len(t):
            break
        i = max(j - CHUNK_OVERLAP, i + 1)
    return [c for c in out if len(c) > 80]


# Gisements documentaires locaux fouilles a chaque demande. AUCUN reseau :
# tout est deja sur le disque, moissonne par les passes precedentes. L'ordre
# compte peu, le plafond par gisement si — sans lui, une question contenant
# « jarvis » ingererait la moitie du disque avant la premiere reponse.
GISEMENTS = [
    ("biblio", "/home/pamerys/jarvis/data/biblio_knowledge", ("*.md",)),
    ("histo", "/home/pamerys/jarvis/data/histo", ("*.md",)),
    ("docs", "/home/pamerys/jarvis/docs", ("*.md",)),
    ("board", "/home/pamerys/jarvis/board", ("*.md",)),
    ("skills", "/home/pamerys/jarvis/.claude/skills", ("*/SKILL.md",)),
    ("remember", "/home/pamerys/jarvis/.remember", ("*.md",)),
    # Gisements de la machine M4 (ajoutes 2026-08-15). Le board ne lisait que
    # ~/jarvis et ignorait la bibliotheque et les memoires, qui sont les
    # sources les plus a jour sur l'etat reel du systeme.
    ("labo", "/home/pamerys/labo", ("*.md",)),
    ("biblio-labo", "/home/pamerys/labo/bibliotheque", ("*.md", "*/*.md", "*/*/*.md")),
    ("memoires", "/home/pamerys/.claude/projects/-home-pamerys-labo/memory", ("*.md",)),
]
MAX_PAR_GISEMENT = 8  # plafond DUR par gisement et par demande

# Chemins JAMAIS moissonnes, quelle que soit la pertinence par mots-cles.
# Le corpus est relu et cite mot pour mot dans les reponses : y faire entrer
# des donnees personnelles (dossier de surendettement, pieces famille,
# identifiants) les rendrait recitables par n'importe quelle question. Le
# filtre porte sur le chemin absolu RESOLU, donc un lien symbolique pointant
# vers une zone interdite est bloque lui aussi.
EXCLUSIONS = (
    "/home/pamerys/labo/docs",  # PII famille, dossier creanciers
    "/home/pamerys/labo/_admin-prive",  # sorties administratives privees
    "/home/pamerys/labo/prospection-b2b/_prive",
    "/home/pamerys/labo/prospection-whatsapp",
    "/.git/",
    "/node_modules/",
)

# La PII n'est pas toujours rangee dans un dossier dedie : a la racine de
# ~/labo cohabitent des fiches administratives nominatives (INPI, SIREN,
# pieces a signer, attestations) et de la documentation technique. Exclure le
# repertoire entier priverait le board de sources utiles ; on filtre donc
# aussi par nom de fichier.
NOMS_INTERDITS = (
    "DOSSIER-INPI",
    "DOSSIER-IMMATRICULATION",
    "PIECES-INPI",
    "ATTESTATION-",
    "CV_",
    "CV-",
)


# Identifiants nominatifs. Le filtre par dossier et par nom ne suffit pas : les
# memoires du projet et des notes a la racine de ~/labo citent le SIREN et le
# numero INPI au milieu de contenu technique parfaitement legitime. Il faut donc
# aussi regarder DANS le fichier. Enjeu reel depuis que le board peut router vers
# un backend cloud : un extrait cite quitte alors la machine.
PII_CONTENU = re.compile(
    r"815353966|J00248088536|J00260620299|25/00351|surendettement", re.I
)


def contient_pii(chemin) -> bool:
    """Vrai si le FICHIER contient un identifiant nominatif."""
    try:
        return bool(PII_CONTENU.search(Path(chemin).read_text(errors="ignore")))
    except OSError:
        return True  # illisible => on s'abstient


def zone_interdite(chemin) -> bool:
    """Vrai si le fichier releve de donnees personnelles (dossier OU nom)."""
    try:
        p = str(Path(chemin).resolve())
    except OSError:
        return True  # illisible => on s'abstient plutot que de risquer
    if any(p.startswith(x) or x in p for x in EXCLUSIONS):
        return True
    return any(Path(p).name.startswith(n) for n in NOMS_INTERDITS)


def nourrir(domain: str, question: str, verbeux: bool = True) -> int:
    """Alimente le domaine en documentation pertinente AVANT de deliberer.

    Le board ne peut raisonner que sur ce qu'il a lu. Attendre une ingestion
    manuelle, c'est garantir qu'il repondra un jour sur un corpus perime : la
    question arrive, le corpus date d'hier, et personne ne voit l'ecart. Ici
    chaque demande declenche une fouille par mots-cles des gisements LOCAUX et
    ingere ce qui manque — dedoublonne par sha256, donc re-fouiller ne coute
    rien quand rien n'a change.

    Zero reseau, zero API, zero token : on relit du disque deja moissonne.
    """
    mots = [m for m in re.findall(r"\w{4,}", question.lower())][:10]
    if not mots:
        return 0
    c = con()
    connus = {r[0] for r in c.execute("SELECT content_sha256 FROM sources")}
    c.close()

    candidats: list[tuple[int, Path]] = []
    for _nom, racine, motifs in GISEMENTS:
        base = Path(racine)
        if not base.is_dir():
            continue
        trouves: list[tuple[int, Path]] = []
        for motif in motifs:
            for f in base.glob(motif):
                if not f.is_file() or f.stat().st_size > 400_000:
                    continue
                if zone_interdite(f) or contient_pii(f):
                    continue  # PII : jamais ingere, meme tres pertinent
                try:
                    txt = f.read_text(errors="ignore").lower()
                except Exception:
                    continue
                if len(txt.strip()) < 120:
                    continue
                # Le score est le nombre de mots DISTINCTS de la question presents,
                # pas le total des occurrences : un fichier qui repete dix fois un
                # seul mot-cle est moins pertinent qu'un fichier qui en couvre trois.
                score = sum(1 for m in set(mots) if m in txt)
                if score >= 2:
                    trouves.append((score, f))
        trouves.sort(key=lambda t: (-t[0], str(t[1])))
        candidats += trouves[:MAX_PAR_GISEMENT]

    neuf = 0
    for _score, f in candidats:
        try:
            raw = f.read_text(errors="ignore")
        except Exception:
            continue
        if hashlib.sha256(raw.encode()).hexdigest() in connus:
            continue  # deja dans le corpus, sous n'importe quel domaine
        cmd_ingest(domain, str(f), kind="md", silencieux=True)
        neuf += 1

    if verbeux:
        if neuf:
            print(
                f"  alimentation : {len(candidats)} document(s) pertinent(s) trouve(s), "
                f"{neuf} NOUVEAU(X) ingere(s) — mots-cles : {', '.join(sorted(set(mots))[:8])}"
            )
        else:
            print(
                f"  alimentation : {len(candidats)} document(s) pertinent(s), "
                f"tous deja dans le corpus (rien a ingerer)"
            )
    return neuf


def cmd_ingest(domain: str, pattern: str, expert=None, kind="md", silencieux=False):
    files = [
        Path(p) for p in globmod.glob(pattern, recursive=True) if Path(p).is_file()
    ]
    if not files:
        if not silencieux:
            print(f"✗ aucun fichier pour « {pattern} »")
        return
    c = con()
    n_src = n_chk = n_skip = 0
    for f in files:
        try:
            raw = f.read_text(errors="ignore")
        except Exception:
            continue
        if len(raw.strip()) < 120:
            continue
        sha = hashlib.sha256(raw.encode()).hexdigest()
        sid = "s_" + sha[:16]
        if c.execute("SELECT 1 FROM sources WHERE content_sha256=?", (sha,)).fetchone():
            n_skip += 1
            continue  # meme contenu = deja ingere
        title = next(
            (
                l.lstrip("# ").strip()
                for l in raw.splitlines()
                if l.strip() and not l.startswith("---")
            ),
            f.stem,
        )[:200]
        c.execute(
            """INSERT INTO sources(id,domain_id,expert_id,kind,title,local_path,content_sha256)
                     VALUES(?,?,?,?,?,?,?)""",
            (sid, domain, expert, kind, title, str(f), sha),
        )
        for i, ch in enumerate(chunk_text(raw)):
            c.execute(
                """INSERT INTO chunks(id,source_id,domain_id,expert_id,chunk_idx,text,token_count)
                         VALUES(?,?,?,?,?,?,?)""",
                (f"{sid}_{i}", sid, domain, expert, i, ch, len(ch) // 4),
            )
            n_chk += 1
        n_src += 1
    c.commit()
    c.close()
    if not silencieux:
        print(f"✓ {n_src} source(s), {n_chk} chunk(s) · {n_skip} doublon(s) ignore(s)")


def cmd_embed(limit=None, batch=100, domain=None):
    """Vectorise les chunks non encore traites, avec commit INCREMENTAL.

    R4-rag — le CIBLAGE PAR DOMAINE n'est pas un confort d'ergonomie.
    Vectoriser dans l'ordre du disque etale la couverture uniformement : on se
    retrouve avec 11 % partout, c'est-a-dire en dessous du seuil utile PARTOUT,
    et les 9 278 vecteurs ne servent nulle part tout en delogeant de vrais
    extraits BM25. Vectoriser un domaine ENTIER le fait passer au-dessus de
    SEUIL_COUVERTURE et lui rend sa seconde jambe, pendant que les autres
    restent proprement en BM25 seul. A budget egal, concentrer bat repartir.

    Un commit unique en fin de boucle n'ecrit rien avant la toute derniere
    ligne : pendant tout le traitement `SELECT COUNT(*) WHERE embedding IS NOT
    NULL` renvoie 0, on ne sait pas si ca progresse ou si c'est bloque, et une
    interruption a 2999/3000 perd les 2999. On commit donc par lots : la
    progression est observable de l'exterieur et reprenable.

    Deux gardes s'appuient sur ce decoupage en lots : la temperature GPU est
    relevee AVANT chaque lot (deux cartes sans ventilateur), et les echecs
    sont ventiles par cause en fin de lot — un `None` muet ne disait pas
    quoi reprendre.
    """
    c = con()
    q = "SELECT id,text FROM chunks WHERE embedding IS NULL"
    params: tuple = ()
    if domain:
        q += " AND domain_id=?"
        params = (domain,)
    if limit:
        q += f" LIMIT {int(limit)}"
    rows = c.execute(q, params).fetchall()
    if not rows:
        print("✓ tous les chunks sont deja vectorises")
        c.close()
        return
    n_par = max(1, int(os.environ.get("BOARD_EMBED_PAR", "4")))
    n_lot = max(1, int(os.environ.get("BOARD_EMBED_LOT", "32")))
    print(
        f"  vectorisation de {len(rows)} chunk(s) — {n_par} en parallele, "
        f"lots API de {n_lot}, commit tous les {batch}"
    )
    ok = traites = 0
    echecs: dict[str, int] = {}
    arret = None  # temperature relevee si on s'arrete pour cause de chauffe
    # 2026-08-18 — garde anti-tourne-a-vide. Sans elle, un backend qui evince son
    # modele en plein vol (« Model was unloaded while the request was still in
    # queue ») faisait echouer 100 % des lots SANS que rien ne le signale : la ligne
    # de progression n'affichait que les succes, et la campagne a brule 80 662
    # tentatives d'affilee avant qu'on s'en apercoive. Desormais on compte les lots
    # consecutifs sans un seul vecteur, et on s'arrete en disant pourquoi.
    vides_consecutifs = 0
    VIDES_MAX = int(os.environ.get("BOARD_EMBED_VIDES_MAX", "5"))
    stop_vide = False
    with ThreadPoolExecutor(max_workers=n_par) as pool:
        for debut in range(0, len(rows), batch):
            t = gpu_temp_max()
            if t is not None and t >= GPU_TEMP_MAX:
                arret = t
                break  # sortie propre : ce qui est deja commite reste acquis
            lot = rows[debut : debut + batch]
            sous_lots = [lot[i : i + n_lot] for i in range(0, len(lot), n_lot)]
            vecs: list = []
            for res in pool.map(
                lambda g: embed_lot([x["text"] for x in g], role="document"), sous_lots
            ):
                vecs.extend(res)
            for r, v in zip(lot, vecs):
                traites += 1
                if v:
                    c.execute(
                        "UPDATE chunks SET embedding=?,embedding_dim=?,embedding_model=? WHERE id=?",
                        (to_blob(v), len(v), EMBED_MODEL, r["id"]),
                    )
                    ok += 1
                else:
                    echecs[v.cause] = echecs.get(v.cause, 0) + 1
            c.commit()
            rate = len(lot) - sum(1 for r, v in zip(lot, vecs) if v)
            vides_consecutifs = vides_consecutifs + 1 if rate == len(lot) else 0
            detail = f" — {rate} echec(s)" if rate else ""
            print(f"    {traites}/{len(rows)} — {ok} vectorises{detail} (commit)", flush=True)
            if vides_consecutifs >= VIDES_MAX:
                stop_vide = True
                break
    c.commit()
    c.close()
    if stop_vide:
        motif = max(echecs, key=echecs.get) if echecs else "cause inconnue"
        print(
            f"\n⛔ ARRET : {VIDES_MAX} lots consecutifs sans un seul vecteur.\n"
            f"   cause dominante : {motif}\n"
            f"   {ok} vectorises, {traites - ok} echecs sur cette campagne.\n"
            f"   Le backend {LMS} ne sert plus d'embeddings de facon fiable.\n"
            "   Verifier qu'il n'evince pas le modele : curl -s "
            f"{LMS.rsplit('/v1', 1)[0]}/api/v0/models",
            flush=True,
        )
    print(f"✓ {ok}/{traites} vectorises")
    if echecs:
        # Sans cette ventilation, un lot a 231/250 ne dit pas QUOI reprendre.
        print(
            "  echecs : "
            + " · ".join(
                f"{n} {cause}"
                for cause, n in sorted(echecs.items(), key=lambda kv: (-kv[1], kv[0]))
            )
        )
    if arret is not None:
        print(
            f"  ⚠ arret thermique : {arret} °C >= {GPU_TEMP_MAX} °C — "
            f"{len(rows) - traites} chunk(s) non traites, relancer une fois refroidi"
        )


# ─────────────────────────────────────────────────────────── recherche
def retrieve(c, domain: str, question: str, k: int = 6) -> list[sqlite3.Row]:
    """Hybride : BM25 lexical + cosine vectoriel, fusionnes par rang.

    Les deux voies ratent des choses differentes — le lexical rate les
    synonymes, le vectoriel rate les identifiants exacts (noms de fichier,
    ports, codes d'erreur). Les fusionner par rang plutot que par score evite
    d'avoir a normaliser deux echelles incomparables.
    """
    scores: dict[str, float] = {}
    lexical_ok = True
    # -- lexical
    # R1-rag — NE PLUS TRONQUER AUX 8 PREMIERS MOTS.
    # Mesure : sur « pourquoi le service est-il en status sigkill apres le
    # sha256 », le `[:8]` gardait *pourquoi, service, status* et jetait
    # *sigkill*, *sha256* — les seuls termes qui discriminent. La position
    # d'un mot dans une phrase francaise ne dit rien de son pouvoir
    # discriminant : les mots outils viennent en tete, le sujet vient apres.
    # On filtre donc par UTILITE (meme stoplist que la porte d'abstention)
    # au lieu de couper a l'aveugle. Le plafond a 24 subsiste, mais comme
    # garde-fou contre une requete FTS pathologique — pas comme selection.
    toks = [t for t in re.findall(r"\w{3,}", question.lower()) if t not in MOTS_VIDES][
        :24
    ]
    if toks:
        try:
            fts = " OR ".join(toks)
            for rank, r in enumerate(
                c.execute(
                    """
                SELECT ch.id FROM chunks_fts f JOIN chunks ch ON ch.rowid=f.rowid
                WHERE chunks_fts MATCH ? AND ch.domain_id=?
                ORDER BY bm25(chunks_fts) LIMIT 40""",
                    (fts, domain),
                )
            ):
                scores[r["id"]] = scores.get(r["id"], 0) + 1.0 / (60 + rank)
        except sqlite3.OperationalError as e:
            # Ne JAMAIS avaler en silence : sans ce signal, un MATCH devenu
            # invalide ferait fusionner une seule liste au RRF et la reponse
            # sortirait quand meme — moins bonne, sans rien pour le dire.
            # Aujourd'hui rien n'est masque (les mots-cles FTS5 ne sont
            # reconnus qu'en MAJUSCULES et la requete passe par .lower()),
            # mais le jour ou ce .lower() saute, on veut l'apprendre.
            print(f"  ! voie lexicale HORS SERVICE ({e}) — RRF sur le vectoriel seul")
            lexical_ok = False
    # -- vectoriel
    # R2-rag — la voie vectorielle n'est utile que si le domaine est
    # SUFFISAMMENT vectorise. Mesure du rapport 02 : hors du perimetre
    # vectorise, le cosinus ameliore 0 fois sur 60 et DEGRADE 13 fois. La
    # raison est mecanique : les fragments vectorises occupent le haut du
    # classement RRF quel que soit leur contenu, et delogent de vrais
    # extraits trouves par BM25. Sous le seuil, on sert donc le lexical seul
    # — et on le DIT, comme le marqueur [ET]/[OU] de cherche.py : un repli
    # tu se fait passer pour un resultat complet.
    couverture = c.execute(
        "SELECT COUNT(*), SUM(embedding IS NOT NULL) FROM chunks WHERE domain_id=?",
        (domain,),
    ).fetchone()
    total_d, vect_d = (couverture[0] or 0), (couverture[1] or 0)
    taux = (vect_d / total_d) if total_d else 0.0
    if taux < SEUIL_COUVERTURE:
        print(
            f"  ~ voie vectorielle ECARTEE : {taux:.0%} du domaine vectorise "
            f"(< {SEUIL_COUVERTURE:.0%}) — BM25 seul, un cosinus partiel degraderait le classement"
        )
        qv = Embedding(cause="couverture_insuffisante")
    else:
        qv = embed(question, role="query")
    if not qv and getattr(qv, "cause", None) != "couverture_insuffisante":
        # Symetrique de la voie lexicale : une panne backend ne doit pas
        # disparaitre. Sans ce message, le board repond en BM25 seul,
        # cite ses sources, et rien ne distingue ce mode degrade.
        # L'ecartement volontaire (couverture insuffisante) est deja annonce
        # plus haut : le repeter ici le ferait passer pour une PANNE, alors
        # que c'est une decision. Un signal qui crie faux finit ignore.
        print(
            f"  ! voie vectorielle HORS SERVICE ({getattr(qv, 'cause', '?')}) — RRF sur le lexical seul"
        )
    if qv:
        sims = []
        for r in c.execute(
            "SELECT id,embedding FROM chunks WHERE domain_id=? AND embedding IS NOT NULL",
            (domain,),
        ):
            sims.append((cosine(qv, from_blob(r["embedding"])), r["id"]))
        sims.sort(reverse=True)
        for rank, (_, cid) in enumerate(sims[:40]):
            scores[cid] = scores.get(cid, 0) + 1.0 / (60 + rank)
    if not scores:
        return []
    top = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
    ids = [i for i, _ in top]
    rows = c.execute(
        f"""SELECT ch.id,ch.text,s.title,s.local_path
                         FROM chunks ch JOIN sources s ON s.id=ch.source_id
                         WHERE ch.id IN ({",".join("?" * len(ids))})""",
        ids,
    ).fetchall()
    order = {i: n for n, i in enumerate(ids)}
    return sorted(rows, key=lambda r: order[r["id"]])


# ─────────────────────────────────────────────────────────── le board
# R1 — sous ce recouvrement, le board s'abstient. 0.20 = un mot sur cinq de la
# question doit au moins apparaitre dans les extraits. Volontairement bas : le
# but est d'attraper le hors-sujet FRANC (extraits PostgreSQL pour une question
# biblio), pas d'arbitrer la finesse semantique — ca, c'est le travail des
# experts. Monter ce seuil ferait taire le board sur des questions legitimes
# formulees avec d'autres mots que le corpus.
SEUIL_PERTINENCE = 0.20

# R2-rag — en dessous de cette part de chunks vectorises dans le domaine, la
# voie cosinus est ECARTEE. 0.60 vient de la mesure du rapport 02 : tant que
# le perimetre vectorise est minoritaire, ses fragments monopolisent le haut
# du classement RRF (20 % du corpus occupait 78 % du top-6) et delogent 43 %
# des extraits que BM25 avait bien trouves. Le seuil n'est donc pas une
# precaution : c'est le point ou la seconde jambe cesse de boiter.
SEUIL_COUVERTURE = 0.60

# Mots vides francais + verbes/substantifs si generiques qu'ils apparaissent dans
# n'importe quel document technique. Ils gonflaient le recouvrement sans rien
# dire du sujet. Meme role que la stoplist de bloc.sh, meme raison.
#
# Elargie le 2026-08-06 : depuis R1-rag cette liste ne sert plus seulement a
# mesurer la pertinence, elle SELECTIONNE les termes envoyes au FTS. Un mot vide
# oublie n'est donc plus un simple bruit de mesure — il occupe une place dans la
# requete. Le test l'a montre : *est*, *que* et *juste* passaient encore.
# La regex retient les mots de 3 lettres et plus ; les mots de 1-2 lettres
# (le, la, de, du, un, en, et, ou) sont deja ecartes par elle.
MOTS_VIDES = frozenset(
    """avec sans dans pour par sur sous entre vers chez depuis pendant selon
    quelles quelle quels quel quoi comment pourquoi quand combien lequel
    sont etre etait seront soit sera etes suis somme est ont ete sois
    qui que quoi dont lequel laquelle lesquels lesquelles
    mais car ni or donc lors afin sauf hors puis ensuite enfin
    nous vous ils elles lui eux son ses mes tes ton toi moi
    cette cet ces celui celle ceux celles leur leurs notre nos votre vos
    plus moins tres bien mal encore deja aussi donc alors ainsi meme tout
    tous toute toutes autre autres chaque aucun aucune
    juste vraiment tellement beaucoup trop assez jamais toujours souvent parfois
    faire fait faut peut peuvent doit doivent
    technique techniques methode methodes maniere manieres facon facons
    chose choses truc trucs cas exemple exemples""".split()
)

CONSIGNE = (
    "Tu reponds UNIQUEMENT a partir des extraits numerotes fournis. "
    "Cite tes sources en ecrivant [1], [2]… dans le corps du texte. "
    "Si les extraits ne permettent pas de repondre, dis-le franchement et "
    "n'invente rien. 6 lignes maximum."
)

# Un numero seul « [3] », ou une plage « [1-6] » / « [1–6] ». Le motif exige
# que le crochet ne contienne QUE cela : « [2026-08-06] » (deux tirets) et
# « [C] » (libelle d'expert anonymise, que l'arbitre melange aux extraits dans
# le meme texte) ne matchent pas, et ne fabriquent donc pas de fausse citation.
_CITATION = re.compile(r"\[(\d+)(?:\s*[-–]\s*(\d+))?\]")


def indices_citees(txt: str, n_max: int) -> set[int]:
    """Numeros d'extraits REELLEMENT references dans un texte.

    Cherchait uniquement « [n] » litteral. Un modele qui cite tout le corpus
    d'un trait — « [1-6] », forme spontanee malgre la consigne — obtenait donc
    ZERO citation et tombait dans answers_sans_citation : une reponse valide
    declaree invalide, et l'alarme de regression du smoke qui se declenche sur
    une deliberation saine. Constate le 2026-08-06 sur la reponse inf-bench.

    Borne a [1, n_max] : une plage delirante ne peut pas citer un extrait qui
    n'a pas ete soumis.
    """
    vus: set[int] = set()
    for debut, fin in _CITATION.findall(txt):
        a = int(debut)
        b = int(fin) if fin else a
        if b < a:  # « [6-1] » reste une plage, pas un ensemble vide
            a, b = b, a
        vus.update(i for i in range(a, b + 1) if 1 <= i <= n_max)
    return vus


def cmd_ask(domain: str, question: str, k: int = 6, only=None):
    c = con()
    experts = c.execute(
        "SELECT * FROM experts WHERE domain_id=? AND is_arbitre=0", (domain,)
    ).fetchall()
    if only:
        keep = set(only.split(","))
        experts = [e for e in experts if e["id"] in keep]
    if not experts:
        print(f"✗ aucun expert pour le domaine « {domain} »")
        c.close()
        return

    # ALIMENTATION AVANT DELIBERATION — a chaque demande, sans exception.
    # Placee APRES le controle des experts (inutile de moissonner pour un domaine
    # vide) et AVANT retrieve() : les documents ingeres a l'instant doivent etre
    # visibles du FTS de cette requete-ci, pas de la suivante. Les triggers
    # chunks_ai maintiennent chunks_fts en synchrone, donc le lexical les voit
    # tout de suite ; le vectoriel devra attendre un `embed` (les nouveaux chunks
    # ont embedding NULL et sont simplement absents de la voie cosine).
    c.close()
    nourrir(domain, question)
    c = con()

    ctx = retrieve(c, domain, question, k)
    if not ctx:
        # Regle fondatrice : sans corpus, pas de reponse. On s'arrete ici.
        print("✗ aucun extrait du corpus ne correspond — le board ne repond pas.")
        c.close()
        return

    # R1 — PORTE D'ABSTENTION SUR LA PERTINENCE.
    # RRF rend TOUJOURS k extraits : c'est un classement, pas un jugement. Le
    # dernier du corpus sort premier si le corpus n'a rien de mieux. Constate en
    # direct : une question sur la bibliotheque a rendu des extraits PostgreSQL
    # BRIN/B-Tree, et l'arbitre a conclu « convergence massive » sur du
    # hors-sujet. Un rang n'est pas une pertinence.
    # Mesure : part du vocabulaire de la question effectivement presente dans les
    # extraits retenus. C'est grossier, mais c'est un signal INDEPENDANT du rang.
    # Les mots VIDES doivent sortir du calcul. Mesure du 2026-08-06 : la question
    # « quelles sont les techniques de fermentation lactique du chou en saumure
    # hypertonique » posee a un domaine informatique a rendu 38 % de recouvrement
    # — donc PAS d'abstention — alors qu'AUCUN mot du sujet (chou, saumure,
    # fermentation, lactique, hypertonique) n'etait dans le corpus. Les 38 %
    # venaient de « quelles », « sont », « techniques ». La porte mesurait la
    # grammaire francaise, pas le sujet. Un filtre >= 4 lettres ne suffit pas :
    # les mots vides francais utiles sont souvent longs.
    qtok = {t for t in re.findall(r"\w{4,}", question.lower()) if t not in MOTS_VIDES}
    # Sous deux mots porteurs, la mesure n'a plus de sens (un seul mot absent
    # ferait 0 %, un seul present 100 %). On laisse alors passer : c'est aux
    # experts de dire « corpus insuffisant », ils savent le faire.
    if len(qtok) >= 2:
        corpus_txt = " ".join(r["text"] for r in ctx).lower()
        recouvrement = sum(1 for t in qtok if t in corpus_txt) / len(qtok)
        if recouvrement < SEUIL_PERTINENCE:
            print(
                f"✗ ABSTENTION — recouvrement {recouvrement:.0%} < {SEUIL_PERTINENCE:.0%} : "
                f"les extraits les mieux classes ne parlent pas de la question.\n"
                f"  Le board se tait plutot que de deliberer sur du hors-sujet.\n"
                f"  Mots absents du corpus : {', '.join(sorted(t for t in qtok if t not in corpus_txt))[:200]}"
            )
            c.close()
            return
        print(
            f"  pertinence : recouvrement {recouvrement:.0%} du vocabulaire de la question"
        )

    qid = (
        "q_"
        + hashlib.sha256(f"{domain}{question}{time.time()}".encode()).hexdigest()[:16]
    )
    c.execute(
        "INSERT INTO queries(id,domain_id,question,retrieval) VALUES(?,?,?,?)",
        (qid, domain, question, json.dumps({"k": k, "chunks": [r["id"] for r in ctx]})),
    )
    c.execute("UPDATE domains SET query_count=query_count+1 WHERE id=?", (domain,))
    c.commit()

    extraits = "\n\n".join(
        f"[{i + 1}] ({r['title']})\n{r['text'][:900]}" for i, r in enumerate(ctx)
    )
    print(f"\n  question : {question}")
    print(
        f"  corpus   : {len(ctx)} extrait(s) · {len(experts)} expert(s) en parallele\n"
    )

    def interroger(e):
        """Un expert parle. Si SON modele tombe, il bascule sur l'autre.

        CASCADE, pas re-essai : re-interroger le meme modele apres une panne
        donne la meme panne — c'est du temps perdu, pas une seconde chance. On
        change de rang.

        Ce qui rendait la bascule necessaire : 17 experts sont cables sur
        hermes-2-pro-mistral-7b et n'avaient produit que 3 avis au total, contre
        36 pour qwen. Un expert dont le modele tombe ne « repond mal » pas — il
        DISPARAIT du vote. Un board dont 40 % des voix ne s'expriment jamais
        n'est pas un board : c'est le modele rapide qui decide seul, sous
        couvert de pluralite.

        Le modele REELLEMENT utilise est remonte : sans lui, `answers.model`
        enregistrerait le modele demande, pas celui qui a parle, et la table
        mentirait sur qui a vote.
        """
        prefere = modele_de(e)
        # Le secours doit EXISTER sur le noeud : hermes-2-pro-mistral-7b venait
        # de M1 et n'est pas installe sur M6, donc l'echec du modele prefere
        # etait suivi d'un second echec certain. deepseek-r1-qwen3-8b est
        # present et se charge sur cette carte.
        defaut_secours = os.environ.get(
            "BOARD_CHAT_MODEL_SECOURS", "deepseek/deepseek-r1-0528-qwen3-8b"
        )
        secours = CHAT_MODEL if prefere != CHAT_MODEL else defaut_secours
        sys_p = e["lens"] + "\n\n" + CONSIGNE
        usr_p = f"EXTRAITS :\n{extraits}\n\nQUESTION : {question}"

        txt, ms = chat(sys_p, usr_p, model=prefere)
        if not (txt.startswith("[echec backend") or txt == "[reponse vide]"):
            return e, txt, ms, prefere

        txt2, ms2 = chat(sys_p, usr_p, model=secours)
        if txt2.startswith("[echec backend") or txt2 == "[reponse vide]":
            # Les DEUX rangs sont tombes : on rend l'echec du PREMIER, qui porte
            # la cause d'origine. Celle du secours ne dirait que « le repli a
            # aussi echoue », ce qui n'aide personne a diagnostiquer.
            return e, txt, ms + ms2, prefere
        # La CAUSE de la panne etait avalee : « injoignable » sans raison a fait
        # patcher deux fois a l'aveugle (ctx 4096 puis budget de troncature)
        # alors que la vraie cause pouvait etre tout autre (file, timeout, 400).
        print(
            f"   ↪ {e['display_name']} : {prefere} injoignable ({txt[:80]}) → bascule sur {secours}"
        )
        return e, txt2, ms + ms2, secours

    # Concurrence des experts. Mesure 2026-08-14 sur Ollama Cloud : 4 requetes
    # simultanees -> 1 seule reponse, 3 `content` VIDES, en HTTP 200 et sans
    # aucun 429. Le backend distant refuse la concurrence *en silence*, ce qui
    # produit exactement le symptome « 3 experts en panne » sans rien a
    # diagnostiquer. On serialise donc des que le backend n'est pas local.
    n_par = int(os.environ.get("BOARD_ASK_PAR", "0")) or (
        1
        if not CHAT_URL.startswith(
            ("http://127.0.0.1", "http://localhost", "http://10.42.")
        )
        else 4
    )
    resultats = list(
        ThreadPoolExecutor(max_workers=max(1, min(n_par, len(experts)))).map(
            interroger, experts
        )
    )

    for e, txt, ms, mdl in resultats:
        if txt.startswith("[echec backend") or txt == "[reponse vide]":
            # L'expert n'a pas repondu : il n'a pas "mal repondu". Inserer
            # cette ligne polluerait answers_sans_citation, qui mesure la
            # conformite a la regle de citation, pas la sante du backend.
            print(
                f"── {e['display_name']}  ({ms} ms)\n   ⚠ PANNE BACKEND : {txt} — non enregistre"
            )
            continue
        aid = f"a_{qid}_{e['id']}"
        c.execute(
            """INSERT OR REPLACE INTO answers(id,query_id,expert_id,text,model,backend,latency_ms)
                     VALUES(?,?,?,?,?,?,?)""",
            # Le modele REELLEMENT interroge, pas la constante : les experts sont
            # repartis sur plusieurs modeles et « qui a dit quoi » doit rester
            # verifiable en SQL, sinon la delibération n'est plus attribuable.
            # `mdl` = le modele qui a REELLEMENT parle, apres bascule
            # eventuelle. `modele_de(e)` rendait le modele DEMANDE : apres un
            # repli, la base attribuait la reponse au modele tombe.
            (aid, qid, e["id"], txt, mdl, "lmstudio:1234", ms),
        )
        # Une citation par extrait REELLEMENT reference dans le texte : c'est ce
        # lien qui rend la regle verifiable, pas la bonne volonte du modele.
        cites = indices_citees(txt, len(ctx))
        for n, r in enumerate(ctx, 1):
            if n in cites:
                c.execute(
                    """INSERT OR IGNORE INTO citations(id,answer_id,chunk_id,rank)
                             VALUES(?,?,?,?)""",
                    (f"c_{aid}_{n}", aid, r["id"], n),
                )
        print(f"── {e['display_name']}  ({ms} ms)")
        print("   " + txt.replace("\n", "\n   ") + "\n")
    c.commit()

    arb = c.execute(
        "SELECT * FROM experts WHERE domain_id=? AND is_arbitre=1 LIMIT 1", (domain,)
    ).fetchone()
    if arb:
        # R2 + R3 — l'arbitre juge des ARGUMENTS, pas des reputations ni des rangs.
        #   R3 anonymise : avec les noms, l'arbitre suit l'expert au titre le plus
        #     imposant plutot que le raisonnement le mieux etaye.
        #   R2 permute : a nom masque, il reste la POSITION. Le premier avis lu
        #     ancre la synthese (biais de primaute). On melange donc l'ordre a
        #     chaque deliberation.
        # Le melange est seede par la question : deux relances de la MEME question
        # donnent le meme ordre (reproductible, rejouable par le domino), deux
        # questions differentes donnent des ordres differents.
        # Une panne backend n'est PAS un avis. Le `continue` plus haut empeche
        # seulement l'INSERTION en base ; `resultats` contient toujours les
        # tuples en echec, et l'arbitre les lisait comme des positions d'expert.
        # Constate le 2026-08-06 sur q_255b70665c4dcef1 : 3 experts en panne,
        # l'arbitre a rendu « les avis A/B/C signalent un echec backend sans
        # cause [...] ils divergent car les uns voient une panne de debit et
        # l'autre un manque de matrice ». Il a fabrique une divergence entre
        # un vrai raisonnement et trois messages d'erreur.
        anonymes = [
            (e, t, ms)
            for e, t, ms, _mdl in resultats
            if not t.startswith("[echec backend") and t != "[reponse vide]"
        ]
        if not anonymes:
            print(
                "══ pas de SYNTHESE : aucun expert n'a repondu (tous en panne backend)."
            )
            c.close()
            return
        if len(anonymes) < len(resultats):
            print(
                f"   ({len(resultats) - len(anonymes)} expert(s) en panne exclu(s) "
                f"de la synthese — l'arbitre ne voit que les {len(anonymes)} avis reels)"
            )
        random.Random(question).shuffle(anonymes)
        avis = "\n\n".join(
            f"Avis {chr(65 + i)} : {t}" for i, (_, t, _) in enumerate(anonymes)
        )
        # La correspondance reste tracee pour nous, hors du prompt de l'arbitre.
        print(
            "   (ordre soumis a l'arbitre, anonymise : "
            + ", ".join(
                f"{chr(65 + i)}={e['display_name']}"
                for i, (e, _, _) in enumerate(anonymes)
            )
            + ")"
        )
        txt, ms = chat(
            arb["lens"] + "\n\n" + CONSIGNE,
            f"EXTRAITS :\n{extraits}\n\nAVIS DES EXPERTS :\n{avis}\n\n"
            f"QUESTION : {question}\n\nArbitre : ou sont-ils d'accord, ou divergent-ils, que retenir ?",
        )
        if txt.startswith("[echec backend") or txt == "[reponse vide]":
            # Meme regle que pour les experts : une panne backend n'est pas
            # une synthese. L'enregistrer polluait answers_sans_citation —
            # constate en direct, le compteur est passe de 4 a 5.
            print(
                f"══ SYNTHESE — {arb['display_name']}\n   ⚠ PANNE BACKEND : {txt} — non enregistre"
            )
            c.close()
            return
        aid = f"a_{qid}_{arb['id']}"
        c.execute(
            """INSERT OR REPLACE INTO answers(id,query_id,expert_id,text,model,backend,latency_ms,is_synthese)
                     VALUES(?,?,?,?,?,?,?,1)""",
            (aid, qid, arb["id"], txt, modele_de(arb), "lmstudio:1234", ms),
        )
        cites = indices_citees(txt, len(ctx))
        for n, r in enumerate(ctx, 1):
            if n in cites:
                c.execute(
                    "INSERT OR IGNORE INTO citations(id,answer_id,chunk_id,rank) VALUES(?,?,?,?)",
                    (f"c_{aid}_{n}", aid, r["id"], n),
                )
        c.commit()
        print(f"══ SYNTHESE — {arb['display_name']}  ({ms} ms)")
        print("   " + txt.replace("\n", "\n   ") + "\n")

    sans = c.execute(
        "SELECT COUNT(*) n FROM answers_sans_citation a WHERE a.query_id=?", (qid,)
    ).fetchone()["n"]
    print(
        "  sources : "
        + " · ".join(f"[{i + 1}] {r['title'][:44]}" for i, r in enumerate(ctx))
    )
    if sans:
        print(
            f"  ⚠ {sans} reponse(s) SANS citation — a rejeter (vue answers_sans_citation)"
        )
    c.close()


def cmd_status():
    if not DB.exists():
        print("✗ base absente — lancer : board.py init")
        return
    c = con()
    q = lambda s: c.execute(s).fetchone()[0]
    print(f"  base      : {DB}  ({DB.stat().st_size // 1024} Ko)")
    print(f"  domaines  : {q('SELECT COUNT(*) FROM domains')}")
    print(f"  experts   : {q('SELECT COUNT(*) FROM experts')}")
    print(f"  sources   : {q('SELECT COUNT(*) FROM sources')}")
    tot = q("SELECT COUNT(*) FROM chunks")
    emb = q("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
    print(f"  chunks    : {tot}  ({emb} vectorises, {tot - emb} en attente)")
    print(
        f"  questions : {q('SELECT COUNT(*) FROM queries')}"
        f" · reponses {q('SELECT COUNT(*) FROM answers')}"
        f" · citations {q('SELECT COUNT(*) FROM citations')}"
    )
    orphelines = q("SELECT COUNT(*) FROM answers_sans_citation")
    print(f"  {'⚠' if orphelines else '✓'} reponses sans citation : {orphelines}")
    for r in c.execute(
        "SELECT d.id,d.display_name,d.query_count,"
        "(SELECT COUNT(*) FROM experts e WHERE e.domain_id=d.id) ne,"
        "(SELECT COUNT(*) FROM chunks ch WHERE ch.domain_id=d.id) nc "
        "FROM domains d ORDER BY d.id"
    ):
        print(
            f"    · {r['id']:<14} {r['display_name'][:26]:<26} {r['ne']} experts · {r['nc']} chunks · {r['query_count']} questions"
        )
    c.close()


# ─────────────────────────────────────────────────────────── CLI
def main(a: list[str]):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = a[0]
    if cmd == "init":
        con().executescript(SCHEMA.read_text())
        print(f"✓ base initialisee : {DB}")
    elif cmd == "status":
        cmd_status()
    elif cmd == "domain" and len(a) > 2 and a[1] == "add":
        c = con()
        c.execute(
            "INSERT OR REPLACE INTO domains(id,display_name,description) VALUES(?,?,?)",
            (a[2], a[3] if len(a) > 3 else a[2], a[4] if len(a) > 4 else None),
        )
        c.commit()
        print(f"✓ domaine « {a[2]} »")
    elif cmd == "expert" and len(a) > 4 and a[1] == "add":
        c = con()
        c.execute(
            """INSERT OR REPLACE INTO experts(id,domain_id,display_name,lens,is_arbitre)
                                VALUES(?,?,?,?,?)""",
            (a[2], a[3], a[4], a[5], 1 if "--arbitre" in a else 0),
        )
        c.commit()
        print(f"✓ expert « {a[4]} »" + (" (arbitre)" if "--arbitre" in a else ""))
    elif cmd == "ingest" and len(a) > 2:
        ex = a[a.index("--expert") + 1] if "--expert" in a else None
        kd = a[a.index("--kind") + 1] if "--kind" in a else "md"
        cmd_ingest(a[1], a[2], ex, kd)
    elif cmd == "embed":
        cmd_embed(
            a[a.index("--limit") + 1] if "--limit" in a else None,
            int(a[a.index("--batch") + 1]) if "--batch" in a else 100,
            a[a.index("--domain") + 1] if "--domain" in a else None,
        )
    elif cmd == "ask" and len(a) > 2:
        k = int(a[a.index("--k") + 1]) if "--k" in a else 6
        ex = a[a.index("--experts") + 1] if "--experts" in a else None
        cmd_ask(a[1], a[2], k, ex)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
