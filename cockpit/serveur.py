#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS COCKPIT — serveur de l'application de pilotage à distance.

Le téléphone (ou n'importe quel navigateur du tailnet) est la façade ;
tout le travail est fait ici, sur M4, qui tient le cluster :
  · STT français local  (faster-whisper :8789)
  · TTS français local  (piper fr_FR-siwis)
  · 43 applis JARVIS    (~/.local/bin)
  · tour GPU M6         (RJ45 direct 10.42.0.230)
  · téléphone S8        (adb)

Zéro dépendance externe : bibliothèque standard seulement.
"""
import base64, json, os, re, subprocess, sys, tempfile, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

RACINE   = os.path.dirname(os.path.abspath(__file__))
WEB      = os.path.join(RACINE, "web")
PORT     = int(os.environ.get("COCKPIT_PORT", "8600"))
STT_URL  = "http://127.0.0.1:8789"
M6_URL   = "http://10.42.0.230:1234"
SPEAK    = os.path.expanduser("~/jarvis/scripts/speak.sh")
S8_SERIE = os.environ.get("S8_SERIAL", "")
JOURNAL  = os.path.expanduser("~/jarvis/logs/cockpit.log")

def log(m):
    ligne = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(ligne, flush=True)
    try:
        with open(JOURNAL, "a", encoding="utf-8") as f: f.write(ligne + "\n")
    except Exception: pass

def sh(cmd, timeout=45):
    """Commande shell sur M4, dans un shell de login (environnement JARVIS complet)."""
    try:
        r = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, "délai dépassé"
    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────────────────────── téléphone (adb)
def s8():
    if S8_SERIE: return S8_SERIE
    ok, out = sh("adb devices", 10)
    for l in out.splitlines()[1:]:
        p = l.split()
        if len(p) >= 2 and p[1] == "device" and not p[0].startswith("emulator-"):
            return p[0]
    return None

def adb(args, timeout=25):
    s = s8()
    if not s: return False, "téléphone absent"
    return sh(f"adb -s {s} {args}", timeout)

# ─────────────────────────────────────────────────────────────── tour GPU M6
OLLAMA_URL = "http://127.0.0.1:11434"

def _nettoie(t):
    """Retire un éventuel bloc de raisonnement laissé par le modèle."""
    t = re.sub(r"<think>.*?</think>", "", t, flags=re.S)
    t = re.sub(r"^\s*(Okay|Alright|First|Let me|The user|I need)\b.*?(?=\n\n|$)", "", t,
               flags=re.S | re.I)
    return t.strip()

def m6_demande(question, timeout=200):
    """Cascade d'inférence locale, 0 token facturé (LOI 2) :
         1. M6 · qwen3.5-9b  — tour GPU, meilleure qualité
         2. M4 · gemma3:4b   — repli local si M6 traîne ou tombe
       Aucun repli codé en dur : si les deux échouent, on le dit."""
    corps = json.dumps({
        "model": "qwen/qwen3.5-9b",
        "prompt": ("<|im_start|>user\n" + question +
                   "\nRéponds en français, clairement et brièvement.<|im_end|>\n"
                   "<|im_start|>assistant\n<think></think>"),
        "max_tokens": 700, "temperature": 0.3, "stop": ["<|im_end|>"],
    }).encode()
    try:
        req = urllib.request.Request(M6_URL + "/v1/completions", data=corps,
                                     headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        t = _nettoie(d["choices"][0].get("text", ""))
        if t:
            log("réponse par M6 (qwen3.5-9b)")
            return t
        log("M6 a renvoyé du vide → repli Ollama M4")
    except Exception as e:
        log(f"M6 indisponible ({e}) → repli Ollama M4")

    try:
        corps = json.dumps({"model": "gemma3:4b", "stream": False,
                            "prompt": question + "\nRéponds en français, brièvement."}).encode()
        req = urllib.request.Request(OLLAMA_URL + "/api/generate", data=corps,
                                     headers={"Content-Type": "application/json"})
        t = _nettoie(json.loads(urllib.request.urlopen(req, timeout=150).read()).get("response", ""))
        if t:
            log("réponse par Ollama M4 (gemma3:4b)")
            return t
    except Exception as e:
        log(f"Ollama M4 indisponible : {e}")
    return ""

# ─────────────────────────────────────────────────────────────── état du cluster
def etat():
    e = {"heure": time.strftime("%H:%M"), "date": time.strftime("%d/%m/%Y")}

    ok, out = sh("uptime | grep -oE 'average:.*' ; free -h | awk '/Mem:/{print $3\"|\"$2}'", 15)
    charge, ram = "?", "?"
    for l in out.splitlines():
        m = re.search(r"average:\s*([0-9.,]+)", l)
        if m: charge = m.group(1)
        if "|" in l: ram = l.replace("|", " / ")
    e["m4"] = {"nom": "M4 · pamerys-m4", "charge": charge, "ram": ram, "en_ligne": ok}

    ok, out = sh("nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,"
                 "temperature.gpu --format=csv,noheader 2>/dev/null", 15)
    e["m4"]["gpu"] = [x.strip() for x in out.splitlines() if x.strip()] if ok else []

    ok, out = sh("ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 -o ConnectTimeout=6 "
                 "turbo@10.42.0.230 'nvidia-smi --query-gpu=name,utilization.gpu,"
                 "memory.used,memory.total,temperature.gpu --format=csv,noheader'", 25)
    cartes = []
    if ok:
        for l in out.splitlines():
            c = [x.strip() for x in l.split(",")]
            if len(c) >= 5:
                cartes.append({"nom": c[0].replace("NVIDIA GeForce ", ""), "charge": c[1],
                               "vram": f"{c[2]} / {c[3]}", "temp": c[4]})
    e["m6"] = {"nom": "M6 · tour GPU", "en_ligne": ok, "cartes": cartes}
    try:
        urllib.request.urlopen(M6_URL + "/v1/models", timeout=6)
        e["m6"]["lmstudio"] = True
    except Exception:
        e["m6"]["lmstudio"] = False

    s = s8()
    e["s8"] = {"en_ligne": bool(s), "serie": s or ""}
    if s:
        ok, b = adb("shell dumpsys battery", 15)
        m = re.search(r"level:\s*(\d+)", b or "")
        e["s8"]["batterie"] = m.group(1) if m else "?"
    return e

# ─────────────────────────────────────────────────────────────── nouvelles / suivi
def nouvelles():
    n = []
    ok, out = sh("sqlite3 -cmd '.timeout 6000' ~/jarvis/jarvis_master.db "
                 "\"SELECT statut||' '||COUNT(*) FROM skillmp_cascade_taches GROUP BY statut;\"", 20)
    if ok and out:
        n.append({"titre": "Cascade SkillsMP",
                  "detail": " · ".join(l.strip() for l in out.splitlines() if l.strip())})
    ok, out = sh("sqlite3 -cmd '.timeout 6000' ~/jarvis/jarvis_master.db "
                 "\"SELECT SUM(installe_claude)||' / '||COUNT(*) FROM skillsmp_affectation;\"", 20)
    if ok and out.strip():
        n.append({"titre": "Skills installés", "detail": out.strip()})
    ok, out = sh("systemctl --failed --no-legend 2>/dev/null | wc -l", 15)
    if ok:
        v = out.strip()
        n.append({"titre": "Services en échec", "detail": v if v != "0" else "aucun"})
    ok, out = sh("df -h / | tail -1 | awk '{print $4\" libres (\"$5\" utilisé)\"}'", 15)
    if ok: n.append({"titre": "Disque M4", "detail": out.strip()})
    ok, out = sh("tailscale status 2>/dev/null | wc -l", 15)
    if ok: n.append({"titre": "Nœuds Tailscale", "detail": out.strip()})
    return n

# ─────────────────────────────────────────────────────────────── routeur vocal
APPLIS = ["board", "table-ronde", "jarvis-audit", "jarvis-heal", "jarvis-crm",
          "jarvis-prospect", "jarvis-skills", "jarvis-turbo-status", "jarvis-swarm"]

def router(texte):
    """Traduit une phrase française en action. Retourne (réponse_parlée, détail_écrit)."""
    t = re.sub(r"\s+", " ", texte.lower().strip())
    t = re.sub(r"[.!?,;]+$", "", t)
    if not t: return "", ""

    # état du cluster — motifs resserrés : le simple mot « cluster »
    # dans une question générale ne doit plus court-circuiter l'IA.
    if (re.search(r"\b(etat|état|status|statut|situation)\b", t)
            or re.search(r"\bcomment (ca|ça) va\b", t)
            or re.search(r"\b(ou|où) (on |en )?en (est|sommes)\b", t)
            or re.search(r"\b(etat|état|sante|santé|charge)\b.*\b(cluster|machine|pc|serveur)\b", t)
            or re.search(r"\b(cluster|machine|pc)\b.*\b(etat|état|va|tourne|repond|répond)\b", t)):
        e = etat()
        p = [f"Le PC tourne, charge {e['m4']['charge']}, mémoire {e['m4']['ram']}."]
        if e["m6"]["en_ligne"]:
            p.append(f"La tour M6 répond avec {len(e['m6']['cartes'])} cartes graphiques.")
        else:
            p.append("La tour M6 ne répond pas.")
        if e["s8"]["en_ligne"]:
            p.append(f"Téléphone connecté, batterie {e['s8'].get('batterie','?')} pour cent.")
        return " ".join(p), json.dumps(e, ensure_ascii=False)

    # GPU
    if (re.search(r"^(les |mes |etat des |état des )?(gpu|cartes?)\b", t)
            or re.search(r"\b(temperature|température|chauffe|surchauffe)\b", t)
            or re.search(r"\bgpu\b.*\b(etat|état|temp|chaud|charge)\b", t)):
        e = etat()
        if not e["m6"]["cartes"]: return "Les cartes de M6 sont injoignables.", ""
        d = " ; ".join(f"{c['nom']} à {c['charge']}, {c['temp']} degrés" for c in e["m6"]["cartes"])
        return "Cartes de M6 : " + d, d

    # nouvelles
    # nouvelles — « résume-moi X » (verbe + complément) doit partir sur l'IA,
    # seule une demande de suivi système atterrit ici.
    if (re.search(r"\b(nouvelles|quoi de neuf|du neuf)\b", t)
            or re.search(r"^(le |un )?(point|rapport|suivi|bilan|resume|résumé)\s*$", t)
            or re.search(r"\b(point|rapport|suivi|bilan)\b.*\b(jarvis|systeme|système|cluster|machine|cascade)\b", t)
            or re.search(r"\b(fais|donne|dis)[- ]moi (le |un )?(point|bilan|rapport|suivi)\b", t)):
        n = nouvelles()
        return ("Voici le point. " + ". ".join(f"{x['titre']} : {x['detail']}" for x in n[:4]),
                json.dumps(n, ensure_ascii=False))

    # lancer une appli JARVIS
    m = re.search(r"\b(?:lance|ouvre|execute|exécute|demarre|démarre)\s+(.+)", t)
    if m:
        cible = m.group(1).strip()
        for a in APPLIS:
            if a.replace("-", " ") in cible or a in cible:
                ok, out = sh(a, 90)
                court = " ".join(out.split())[:400]
                return (f"{a} exécuté." if ok else f"{a} a échoué."), court
        return f"Application {cible} inconnue.", ""

    # commande brute sur le PC
    m = re.search(r"\b(?:sur le pc|commande|shell|terminal)\s+(.+)", t)
    if m:
        ok, out = sh(m.group(1).strip(), 60)
        court = " ".join(out.split())[:400]
        return ("Fait." if ok else "La commande a échoué."), court

    # téléphone
    if re.search(r"\b(capture|screenshot)\b", t):
        ok, _ = adb("shell screencap -p /data/local/tmp/c.png")
        if ok: adb(f"pull /data/local/tmp/c.png {os.path.expanduser('~/jarvis/logs/capture.png')}")
        return ("Capture prise." if ok else "Téléphone absent."), ""

    # tout le reste part sur le GPU M6 (0 token)
    r = m6_demande(texte)
    return (r if r else "La tour M6 n'a pas répondu."), r

# ─────────────────────────────────────────────────────────────── audio
def transcrire(donnees_audio, mime):
    """Audio du navigateur → WAV 16 kHz mono → Whisper local. Retourne le texte."""
    ext = ".webm" if "webm" in mime else (".ogg" if "ogg" in mime else ".wav")
    src = tempfile.mktemp(suffix=ext); wav = tempfile.mktemp(suffix=".wav")
    try:
        open(src, "wb").write(donnees_audio)
        subprocess.run(["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", "-f", "wav", wav],
                       capture_output=True, timeout=60)
        if not os.path.exists(wav) or os.path.getsize(wav) < 1000:
            return ""
        b = base64.b64encode(open(wav, "rb").read()).decode()
        req = urllib.request.Request(STT_URL,
            data=json.dumps({"audio": b, "format": "wav", "language": "fr"}).encode(),
            headers={"Content-Type": "application/json"})
        return (json.loads(urllib.request.urlopen(req, timeout=180).read()).get("text") or "").strip()
    except Exception as e:
        log(f"STT : {e}")
        return ""
    finally:
        for f in (src, wav):
            try: os.unlink(f)
            except Exception: pass

def synthese(texte):
    """Texte → WAV piper (français), renvoyé en base64 pour le navigateur."""
    wav = tempfile.mktemp(suffix=".wav")
    modele = os.path.expanduser("~/jarvis/models/piper/fr_FR-siwis-medium.onnx")
    try:
        p = subprocess.run(["piper", "--model", modele, "--output_file", wav],
                           input=texte[:900].encode(), capture_output=True, timeout=90)
        if os.path.exists(wav) and os.path.getsize(wav) > 100:
            return base64.b64encode(open(wav, "rb").read()).decode()
    except Exception as e:
        log(f"TTS : {e}")
    finally:
        try: os.unlink(wav)
        except Exception: pass
    return ""

# ─────────────────────────────────────────────────────────────── HTTP
class Cockpit(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass

    def _envoi(self, code, corps, ctype="application/json; charset=utf-8"):
        if isinstance(corps, (dict, list)):
            corps = json.dumps(corps, ensure_ascii=False).encode()
        elif isinstance(corps, str):
            corps = corps.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corps)

    def do_OPTIONS(self): self._envoi(204, b"")

    def do_GET(self):
        chemin = urlparse(self.path).path
        if chemin in ("/", "/index.html"): return self._fichier("index.html", "text/html; charset=utf-8")
        if chemin == "/manifest.json":     return self._fichier("manifest.json", "application/manifest+json")
        if chemin == "/sw.js":             return self._fichier("sw.js", "application/javascript")
        if chemin == "/icone.png":         return self._fichier("icone.png", "image/png", binaire=True)
        if chemin == "/api/etat":          return self._envoi(200, etat())
        if chemin == "/api/nouvelles":     return self._envoi(200, nouvelles())
        if chemin == "/api/sante":         return self._envoi(200, {"ok": True, "heure": time.strftime("%H:%M:%S")})
        self._envoi(404, {"erreur": "inconnu"})

    def _fichier(self, nom, ctype, binaire=False):
        p = os.path.join(WEB, nom)
        if not os.path.exists(p): return self._envoi(404, {"erreur": nom})
        with open(p, "rb") as f: d = f.read()
        self._envoi(200, d if binaire else d.decode(), ctype)

    def do_POST(self):
        chemin = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0))
        brut = self.rfile.read(n) if n else b""

        if chemin == "/api/vocal":
            texte = transcrire(brut, self.headers.get("Content-Type", ""))
            if not texte:
                return self._envoi(200, {"texte": "", "reponse": "Je n'ai rien entendu.",
                                         "audio": synthese("Je n'ai rien entendu.")})
            log(f"🎙 « {texte} »")
            parle, detail = router(texte)
            return self._envoi(200, {"texte": texte, "reponse": parle,
                                     "detail": detail, "audio": synthese(parle)})

        try: corps = json.loads(brut.decode() or "{}")
        except Exception: corps = {}

        if chemin == "/api/texte":
            q = (corps.get("texte") or "").strip()
            if not q: return self._envoi(200, {"reponse": ""})
            log(f"⌨ « {q} »")
            parle, detail = router(q)
            return self._envoi(200, {"texte": q, "reponse": parle, "detail": detail,
                                     "audio": synthese(parle) if corps.get("voix") else ""})

        if chemin == "/api/exec":
            ok, out = sh(corps.get("commande", ""), 120)
            return self._envoi(200, {"ok": ok, "sortie": out[:8000]})

        if chemin == "/api/m6":
            r = m6_demande(corps.get("question", ""))
            return self._envoi(200, {"reponse": r, "audio": synthese(r) if corps.get("voix") else ""})

        self._envoi(404, {"erreur": "inconnu"})

if __name__ == "__main__":
    log(f"JARVIS COCKPIT sur 0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Cockpit).serve_forever()
