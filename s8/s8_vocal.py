#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS-S8 VOCAL — pilotage 100 % à la voix du Samsung Galaxy S8 (tactile HS).
Identité pamerys / M4. 0-token : tout est local (faster-whisper 8789 + piper).

Chaîne : micro M4 -> [wake word "hey jarvis"] -> VAD silence -> STT local 8789
         -> routeur de commandes -> adb/scrcpy sur le S8 -> retour vocal piper.

Aucun appel cloud. Aucune touche à effleurer sur le téléphone.
"""
import os, sys, json, time, base64, wave, subprocess, tempfile, threading, queue, re, shutil
import urllib.request

# ----------------------------------------------------------------------------- config
STT_URL      = os.environ.get("S8_STT_URL", "http://127.0.0.1:8789")
SPEAK        = os.path.expanduser("~/jarvis/scripts/speak.sh")
LOG          = os.path.expanduser("~/jarvis/logs/s8_vocal.log")
SERIAL       = os.environ.get("S8_SERIAL", "")          # vide = auto-détection
ALSA_MIC     = os.environ.get("S8_ALSA_MIC", "plughw:CARD=PCH,DEV=0")
SAMPLE_RATE  = 16000
SILENCE_RMS  = float(os.environ.get("S8_SILENCE_RMS", "0.012"))
SILENCE_SEC  = float(os.environ.get("S8_SILENCE_SEC", "1.1"))
MAX_SEC      = float(os.environ.get("S8_MAX_SEC", "20"))
WAKE_ENABLED = os.environ.get("S8_WAKE", "1") == "1"
WAKE_MODEL   = "hey_jarvis"

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")
    except Exception: pass

def dire(texte):
    """Retour vocal français (piper local, 0-token)."""
    log(f"🔊 {texte}")
    try:
        subprocess.run([SPEAK, texte], timeout=45,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log(f"   (TTS indisponible: {e})")

def bip():
    """Court accusé sonore : le micro est ouvert."""
    try:
        subprocess.run(["play", "-nq", "-t", "alsa", "synth", "0.09", "sine", "880", "vol", "0.25"],
                       timeout=4, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception: pass

# ----------------------------------------------------------------------------- S8 / adb
def s8_serial():
    """Retourne le serial du S8 connecté, ou None. Ignore les émulateurs fantômes."""
    if SERIAL: return SERIAL
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=8).stdout
    except Exception:
        return None
    for ligne in out.splitlines()[1:]:
        p = ligne.split()
        if len(p) >= 2 and p[1] == "device" and not p[0].startswith("emulator-"):
            return p[0]
    return None

def adb(*args, timeout=25):
    """Exécute une commande adb sur le S8. Retourne (ok, sortie)."""
    s = s8_serial()
    if not s:
        return False, "S8_ABSENT"
    try:
        r = subprocess.run(["adb", "-s", s, *args], capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr).strip()
    except Exception as e:
        return False, str(e)

def adb_texte(txt):
    """Injecte du texte dans le champ actif du S8 (espaces -> %s, échappement shell)."""
    safe = txt.replace("\\", "\\\\")
    for c in ['"', "'", "&", "<", ">", ";", "|", "(", ")", "`", "$"]:
        safe = safe.replace(c, "\\" + c)
    safe = safe.replace(" ", "%s")
    return adb("shell", f'input text "{safe}"')

TOUCHES = {
    "entree": 66, "entrée": 66, "valide": 66, "valider": 66,
    "retour": 4, "arriere": 4, "arrière": 4,
    "accueil": 3, "home": 3,
    "menu": 82, "recents": 187, "récents": 187,
    "haut": 19, "bas": 20, "gauche": 21, "droite": 22,
    "effacer": 67, "supprimer": 67, "backspace": 67,
    "tabulation": 61, "tab": 61, "espace": 62, "echap": 111, "échap": 111,
    "volume plus": 24, "volume moins": 25, "allumer": 26, "eteindre": 26, "éteindre": 26,
}


# ----------------------------------------------------------------------------- cluster
def pc(commande, timeout=40):
    """Exécute une commande sur le PC M4 (local — le daemon tourne déjà dessus)."""
    try:
        r = subprocess.run(["bash", "-lc", commande], capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr).strip()
    except Exception as e:
        return False, str(e)

def m6_demande(question, timeout=120):
    """Interroge qwen3.5-9b sur M6 (GPU, 0 token facturé).
    Parade au reasoning-runaway : /v1/completions + bloc <think></think> pré-rempli."""
    corps = json.dumps({
        "model": "qwen/qwen3.5-9b",
        "prompt": ("<|im_start|>user\n" + question +
                   " Réponds en français, en 2 phrases maximum.<|im_end|>\n"
                   "<|im_start|>assistant\n<think></think>"),
        "max_tokens": 300, "temperature": 0.3, "stop": ["<|im_end|>"],
    }).encode()
    try:
        req = urllib.request.Request("http://10.42.0.230:1234/v1/completions",
                                     data=corps, headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        return d["choices"][0].get("text", "").strip()
    except Exception as e:
        log(f"❌ M6: {e}")
        return ""

# ----------------------------------------------------------------------------- routeur
def normalise(t):
    t = t.lower().strip()
    t = re.sub(r"[.!?,;]+$", "", t)
    return re.sub(r"\s+", " ", t)

def router(texte):
    """Traduit une phrase française en action réelle. Retourne la phrase de retour vocal."""
    t = normalise(texte)
    if not t:
        return None

    # --- CLUSTER : interroger M6 (GPU, 0 token) ---------------------------------
    m = re.search(r"\b(?:demande|questionne|interroge)\s+(?:a|à)\s+(?:m6|em six|la tour)\s+(.+)", t)
    if not m:
        m = re.search(r"\b(?:m6|em six)\s+(.+)", t)
    if m:
        question = m.group(1).strip()
        rep = m6_demande(question)
        return rep if rep else "M6 n'a pas répondu."

    # --- CLUSTER : état des GPU -------------------------------------------------
    if re.search(r"\b(gpu|carte graphique|cartes graphiques|temperature|température)\b", t):
        ok, sortie = pc("ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 turbo@10.42.0.230 "
                        "'nvidia-smi --query-gpu=name,utilization.gpu,temperature.gpu --format=csv,noheader'")
        if not ok or not sortie:
            return "Les GPU de M6 sont injoignables."
        lignes = [l for l in sortie.splitlines() if l.strip()][:4]
        parts = []
        for l in lignes:
            c = [x.strip() for x in l.split(",")]
            if len(c) >= 3:
                parts.append(f"{c[0].replace('NVIDIA GeForce ','')} à {c[1]}, {c[2]} degrés")
        return "GPU de M6 : " + " ; ".join(parts) if parts else "Aucun GPU lu."

    # --- CLUSTER : état général -------------------------------------------------
    if re.search(r"\b(cluster|le pc|machine|charge|m4)\b", t) and re.search(r"\b(etat|état|status|comment|charge)\b", t):
        ok, sortie = pc("hostname; uptime; free -h | awk '/Mem:/{print $3\" sur \"$2}'")
        if not ok:
            return "Le PC ne répond pas."
        l = [x for x in sortie.splitlines() if x.strip()]
        charge = ""
        for x in l:
            mm = re.search(r"average:?\s*([0-9.,]+)", x)
            if mm: charge = mm.group(1)
        ram = l[-1] if l else "?"
        return f"Le PC M4 répond. Charge {charge}. Mémoire {ram}."

    # --- CLUSTER : lancer une commande sur le PC --------------------------------
    m = re.search(r"\b(?:sur le pc|sur m4|sur l ordinateur)\s+(.+)", t)
    if m:
        ok, sortie = pc(m.group(1).strip())
        if not ok: return "Le PC ne répond pas."
        court = " ".join(sortie.split())[:300]
        return court if court else "Commande exécutée sur le PC."

    # --- COCKPIT ----------------------------------------------------------------
    if re.search(r"\b(cockpit|tableau de bord|poste de commande)\b", t):
        ok, _ = adb_texte("cockpit")
        if not ok: return "S8 non connecté."
        adb("shell", "input keyevent 66")
        return "Cockpit affiché sur le téléphone."

    # --- état / diagnostic ------------------------------------------------------
    if re.search(r"\b(etat|état|status|statut|connecte|connecté|diagnostic)\b", t):
        s = s8_serial()
        if not s:
            return "Le S8 n'est pas connecté. Branche le câble USB."
        ok, modele = adb("shell", "getprop ro.product.model")
        ok2, bat = adb("shell", "dumpsys battery | grep level")
        niveau = re.search(r"\d+", bat).group(0) if ok2 and re.search(r"\d+", bat) else "?"
        return f"S8 connecté. Modèle {modele}. Batterie {niveau} pour cent."

    # --- écran miroir : LA réponse au tactile HS --------------------------------
    if re.search(r"\b(scrcpy|miroir|ecran|écran|affiche le telephone|affiche le téléphone|prends la main)\b", t):
        if not s8_serial():
            return "Impossible, le S8 n'est pas connecté."
        subprocess.Popen(["scrcpy", "--stay-awake", "--turn-screen-off", "--window-title", "JARVIS-S8"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Écran du S8 ouvert sur le M4. Utilise la souris et le clavier du PC."

    # --- capture d'écran --------------------------------------------------------
    if re.search(r"\b(capture|screenshot|photo de l'ecran|photo de l'écran)\b", t):
        dest = os.path.expanduser(f"~/jarvis/logs/s8_{time.strftime('%H%M%S')}.png")
        ok, _ = adb("shell", "screencap -p /data/local/tmp/s.png")
        if not ok: return "Capture impossible, S8 non connecté."
        adb("pull", "/data/local/tmp/s.png", dest)
        return "Capture d'écran enregistrée."

    # --- lancer une application -------------------------------------------------
    m = re.search(r"\b(?:ouvre|lance|demarre|démarre)\s+(.+)", t)
    if m:
        cible = m.group(1).strip()
        paquets = {
            "termux": "com.termux/.app.TermuxActivity",
            "terminal": "com.termux/.app.TermuxActivity",
            "parametres": "com.android.settings/.Settings",
            "paramètres": "com.android.settings/.Settings",
            "reglages": "com.android.settings/.Settings",
            "réglages": "com.android.settings/.Settings",
        }
        for cle, comp in paquets.items():
            if cle in cible:
                ok, _ = adb("shell", f"am start -n {comp}")
                return f"{cle} ouvert." if ok else "S8 non connecté."
        return f"Application {cible} inconnue. Dis : ouvre termux, ou ouvre paramètres."

    # --- touches physiques ------------------------------------------------------
    for mot, code in sorted(TOUCHES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(mot)}\b", t):
            ok, _ = adb("shell", f"input keyevent {code}")
            return f"{mot}." if ok else "S8 non connecté."

    # --- envoyer une question à Claude Code sur le S8 ---------------------------
    m = re.search(r"\b(?:claude|jarvis)\s+(.+)", t)
    if m:
        q = m.group(1).strip()
        ok, _ = adb_texte(q)
        if not ok: return "S8 non connecté."
        adb("shell", "input keyevent 66")
        return "Question envoyée à Claude Code."

    # --- dictée explicite -------------------------------------------------------
    m = re.search(r"\b(?:ecris|écris|tape|dicte|saisis)\s+(.+)", t)
    if m:
        ok, _ = adb_texte(m.group(1).strip())
        return "Texte saisi." if ok else "S8 non connecté."

    # --- exécuter une commande shell sur le S8 ---------------------------------
    m = re.search(r"\b(?:commande|execute|exécute|shell)\s+(.+)", t)
    if m:
        ok, _ = adb_texte(m.group(1).strip())
        if not ok: return "S8 non connecté."
        adb("shell", "input keyevent 66")
        return "Commande exécutée sur le S8."

    # --- arrêt ------------------------------------------------------------------
    if re.search(r"\b(stop|arrete toi|arrête toi|au revoir|termine)\b", t):
        return "__STOP__"

    # --- défaut : on tape le texte tel quel (mode dictée continue) --------------
    ok, _ = adb_texte(texte.strip())
    return "Dicté." if ok else "S8 non connecté. Branche le câble et redis ta commande."

# ----------------------------------------------------------------------------- audio
def transcrire(frames_pcm):
    """Envoie le PCM 16 kHz mono au serveur Whisper local. Retourne le texte français."""
    wav = tempfile.mktemp(suffix=".wav")
    try:
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SAMPLE_RATE)
            w.writeframes(frames_pcm)
        b = base64.b64encode(open(wav, "rb").read()).decode()
        req = urllib.request.Request(STT_URL,
            data=json.dumps({"audio": b, "format": "wav", "language": "fr"}).encode(),
            headers={"Content-Type": "application/json"})
        rep = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
        return (rep.get("text") or "").strip()
    except Exception as e:
        log(f"❌ STT: {e}")
        return ""
    finally:
        try: os.unlink(wav)
        except Exception: pass

def boucle():
    import numpy as np

    wake = None
    if WAKE_ENABLED:
        try:
            import openwakeword
            from openwakeword.model import Model
            res = os.path.join(os.path.dirname(openwakeword.__file__), "resources", "models")
            chemin = os.path.join(res, "hey_jarvis_v0.1.onnx")
            wake = Model(wakeword_model_paths=[chemin])
            log("👂 Mot d'éveil actif : « Hey Jarvis »")
        except Exception as e:
            log(f"⚠️  Mot d'éveil indisponible ({e}) — écoute permanente.")
            wake = None

    dire("Jarvis S8 est prêt. Dis Hey Jarvis, puis ta commande." if wake
         else "Jarvis S8 est prêt. Parle, j'écoute.")

    BLOC = 1280            # 80 ms @16 kHz — taille attendue par openwakeword
    OCTETS = BLOC * 2

    # PulseAudio/PipeWire est cassé sur M4 : on attaque ALSA en direct, comme speak.sh.
    micro = subprocess.Popen(
        ["arecord", "-D", ALSA_MIC, "-f", "S16_LE", "-r", str(SAMPLE_RATE),
         "-c", "1", "-t", "raw", "-q", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=OCTETS * 4)

    def lire():
        brut = micro.stdout.read(OCTETS)
        if not brut or len(brut) < OCTETS:
            raise RuntimeError("flux micro interrompu")
        return np.frombuffer(brut, dtype=np.int16)

    try:
        arme = wake is None
        while True:
            mono = lire()

            # ---- attente du mot d'éveil ----
            if not arme:
                try:
                    score = max(wake.predict(mono).values())
                except Exception:
                    score = 0.0
                if score > 0.5:
                    log("🎯 « Hey Jarvis » détecté")
                    bip()
                    arme = True
                    try: wake.reset()
                    except Exception: pass
                continue

            # ---- capture jusqu'au silence ----
            log("🎙️  J'écoute…")
            morceaux, silence, debut = [mono.tobytes()], 0.0, time.time()
            while True:
                m = lire()
                morceaux.append(m.tobytes())
                rms = float(np.sqrt(np.mean((m.astype(np.float32) / 32768.0) ** 2)))
                silence = silence + 0.08 if rms < SILENCE_RMS else 0.0
                if silence >= SILENCE_SEC and time.time() - debut > 1.0: break
                if time.time() - debut > MAX_SEC: break

            texte = transcrire(b"".join(morceaux))
            if not texte:
                log("   (rien compris)")
                arme = wake is None
                continue

            log(f"📝 « {texte} »")
            reponse = router(texte)
            if reponse == "__STOP__":
                dire("À bientôt Turbo."); return
            if reponse:
                dire(reponse)
            arme = wake is None
    finally:
        try: micro.terminate()
        except Exception: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--test", "-t"):
        # Mode test : une phrase passée en argument, sans micro.
        phrase = " ".join(sys.argv[2:])
        print(f"ENTREE  : {phrase}")
        print(f"ACTION  : {router(phrase)}")
        sys.exit(0)
    try:
        boucle()
    except KeyboardInterrupt:
        log("Arrêt demandé.")
