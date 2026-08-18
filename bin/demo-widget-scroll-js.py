#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture du dashboard :8899 avec DÉFILEMENT PILOTÉ EN JAVASCRIPT (window.scrollTo).
Fiable : ne dépend NI de la molette NI du clavier NI du focus (WebKitGTK les ignore).
Une fenêtre WebKit dédiée, keep_above, est filmée par ffmpeg pendant que le JS fait
descendre la page section par section (calé sur la voix off segmentée), atteint le
BAS, puis remonte. Sortie: demo/widget-bureau-<stamp>.mp4"""

import os
import sys
import time
import subprocess
import gi

gi.require_version("Gtk", "3.0")
for v in ("4.1", "4.0"):
    try:
        gi.require_version("WebKit2", v)
        break
    except ValueError:
        continue
from gi.repository import Gtk, WebKit2, Gdk, GLib

DISP = os.environ.get("DISPLAY", ":0")
ENV = {**os.environ, "DISPLAY": DISP}
URL = "http://127.0.0.1:8899/"
WX, WY, WW, WH = 80, 30, 600, 1010
OUTDIR = os.path.expanduser("~/jarvis/demo")
STAMP = time.strftime("%Y%m%d-%H%M%S")
WORK = f"/tmp/wjs-{STAMP}"
os.makedirs(WORK, exist_ok=True)
NARR_MP3 = f"{WORK}/narration.mp3"
SCREEN = f"{WORK}/screen.mp4"
FINAL = f"{OUTDIR}/widget-bureau-{STAMP}.mp4"
VOICE = os.environ.get("VOICE", "fr-FR-DeniseNeural")
CLEAN = os.path.expanduser("~/jarvis/bin/clean_narration.py")

SEGMENTS = [
    (
        "Voici JARVIS OS, une intelligence artificielle autonome qui tourne intégralement "
        "sur une seule machine grand public. Un processeur classique, soixante-quatre gigaoctets "
        "de mémoire, et six cartes graphiques. Ce tableau de bord montre, en direct, "
        "tout ce que le système fait, et tout ce qu'il sait faire.",
        "top",
    ),
    (
        "Toute l'intelligence est locale. Aucune donnée ne quitte la machine, "
        "aucun euro n'est dépensé dans le cloud. Les modèles Qwen, Gemma et Deepseek "
        "tournent sur place, épaulés par un cluster de plusieurs machines qui se réveillent à la demande.",
        "descente",
    ),
    (
        "En haut, un compte à rebours. À intervalle régulier, le système déclenche lui-même sa prochaine action. "
        "La file de tâches se prépare, s'exécute, et se vérifie, sans personne aux commandes.",
        "descente",
    ),
    (
        "D'un seul geste, il exécute toute la file, régénère sa liste de tâches, "
        "remplit sa bibliothèque de connaissances, lance une recherche web en cascade, vectorise ses documents, "
        "déclenche une sauvegarde complète, se répare lui-même, ou démarre la mairie numérique.",
        "descente",
    ),
    (
        "Les compteurs, en direct. Plus de cinq mille tâches accomplies et vérifiées. "
        "Onze mille dominos d'action prêts à l'emploi. Deux cent trente-cinq chaînes d'automatisation. "
        "Et plus de vingt mille déclenchements enregistrés.",
        "descente",
    ),
    (
        "Backlog, file dynamique, tâches en cours, et une colonne essentielle : à valider. "
        "Tout ce qui sort vers l'extérieur, un mail, une publication, un envoi, attend votre accord. "
        "Le système agit seul, mais ne franchit jamais une ligne rouge tout seul.",
        "descente",
    ),
    (
        "Neuf cent soixante et un agents sont indexés, mille quatre cent trente-cinq dans l'écosystème complet, "
        "répartis en couches spécialisées. Administration, marketing, sécurité, opérations système, "
        "et recherche scientifique.",
        "descente",
    ),
    (
        "La gestion du courrier et des mails. Le système lit votre boîte, trie chaque message, "
        "détecte les urgences, qualifie les demandes, prépare les réponses, remplit les formulaires "
        "administratifs, et achemine chaque dossier vers le bon service. "
        "Analyse, détection, validation, cent pour cent automatiques.",
        "descente",
    ),
    (
        "Sa todolist en cascade couvre quatre projets en parallèle, cinquante et une tâches, "
        "chacune avec sa progression suivie en temps réel.",
        "descente",
    ),
    (
        "Le matériel. Six cartes graphiques : quatre GTX seize soixante, "
        "une RTX deux mille soixante, et une RTX trois mille quatre-vingt. "
        "Toutes surveillées en température et en charge, seconde après seconde.",
        "descente",
    ),
    (
        "Des lanceurs d'applications intégrés donnent un accès direct au navigateur, "
        "au module de factures, et au traitement des mails et des démarches.",
        "descente",
    ),
    (
        "Soixante-deux minuteries orchestrent le système, jour et nuit, "
        "chacune avec son prochain déclenchement affiché.",
        "descente",
    ),
    (
        "Plus bas, les dominos. Des milliers d'actions lançables en un seul clic : "
        "audits de sécurité, indexation vectorielle, supervision des workflows, "
        "chaînées entre elles pour se dérouler toutes seules.",
        "descente",
    ),
    (
        "Un terminal web affiche les logs d'exécution en direct. "
        "Une chronologie horodatée trace chaque événement. "
        "Et la production recense toutes les tâches réellement accomplies, preuve à l'appui.",
        "descente",
    ),
    (
        "Le cœur de connexion : soixante-dix serveurs et connecteurs. "
        "Modèles locaux et cloud, mémoire persistante, agents, navigateur, bases de données, "
        "réseaux sociaux, déploiement. Le système parle à tout votre environnement numérique.",
        "descente",
    ),
    (
        "Car voilà tout ce qu'il gère pour vous. Vos dépôts de code et vos publications. "
        "Le trading algorithmique et la veille des marchés. Votre contenu sur les réseaux sociaux, "
        "Instagram, TikTok, YouTube et LinkedIn. Vos mails et vos démarches administratives. "
        "Vos sauvegardes, et la santé de toute votre infrastructure.",
        "descente",
    ),
    (
        "Voilà JARVIS OS. Une intelligence artificielle autonome, souveraine, entièrement locale, "
        "qui produit, communique, administre, et se répare toute seule. "
        "Sur du matériel grand public. Zéro euro de cloud. "
        "Zéro donnée qui sort de la machine. Zéro coût par requête.",
        "conclusion",
    ),
]


def sh(*a, **k):
    return subprocess.run(a, env=ENV, **k)


def dur_of(p):
    return float(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                p,
            ],
            capture_output=True,
            text=True,
        ).stdout.strip()
        or "0"
    )


# ── 1. TTS segmenté + concat + timeline ───────────────────────────────
def build_audio():
    print("🗣️  voix off segmentée…", flush=True)
    durs = []
    concl = next(i for i, (_, r) in enumerate(SEGMENTS) if r == "conclusion")
    listf = f"{WORK}/list.txt"
    lines = []
    SIL = f"{WORK}/sil.mp3"
    sh(
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=mono:sample_rate=24000",
        "-t",
        "2.5",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "4",
        SIL,
        capture_output=True,
    )
    for i, (txt, role) in enumerate(SEGMENTS):
        cl = (
            subprocess.run(
                ["python3", CLEAN], input=txt, capture_output=True, text=True
            ).stdout.strip()
            or txt
        )
        mp3 = f"{WORK}/s{i:02d}.mp3"
        sh(
            "edge-tts",
            "--voice",
            VOICE,
            "--text",
            cl,
            "--write-media",
            mp3,
            capture_output=True,
        )
        if not os.path.exists(mp3) or os.path.getsize(mp3) < 1500:
            print(f"✗ TTS seg {i} échec")
            sys.exit(1)
        if i == concl:
            lines.append(f"file '{SIL}'")
        lines.append(f"file '{mp3}'")
        durs.append(dur_of(mp3))
        print(f"   seg {i} [{role}] {durs[-1]:.1f}s", flush=True)
    open(listf, "w").write("\n".join(lines) + "\n")
    sh(
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        listf,
        "-c:a",
        "libmp3lame",
        "-q:a",
        "4",
        NARR_MP3,
        capture_output=True,
    )
    DUR = dur_of(NARR_MP3)
    T_intro = durs[0]
    T_bas = sum(durs[:concl])
    T_rem = T_bas + 2.5
    print(
        f"   total {DUR:.0f}s · haut→0-{T_intro:.0f} · descente {T_intro:.0f}-{T_bas:.0f} · remontée {T_rem:.0f}-{DUR:.0f}",
        flush=True,
    )
    return DUR, T_intro, T_bas, T_rem


DUR, T_INTRO, T_BAS, T_REM = build_audio()


# ── 2. fenêtre WebKit dédiée (keep_above, visible) ────────────────────
class Cap(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_default_size(WW, WH)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)  # AU-DESSUS (filmable), pas keep_below
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_title("JARVIS Capture")
        self.wv = WebKit2.WebView()
        self.add(self.wv)
        self.wv.load_uri(URL)
        self.connect("destroy", Gtk.main_quit)
        self.connect("realize", lambda *_: self.move(WX, WY))
        self.wv.connect("load-changed", self._on_load)
        self.ff = None
        self.t0 = None
        self.started = False

    def _js(self, code):
        try:
            self.wv.run_javascript(code, None, None, None)
        except Exception:
            try:
                self.wv.evaluate_javascript(code, -1, None, None, None, None, None)
            except Exception:
                pass

    def _on_load(self, wv, ev):
        if ev == WebKit2.LoadEvent.FINISHED and not self.started:
            self.started = True
            self.move(WX, WY)
            GLib.timeout_add(2500, self._start)  # laisse charger les données (/data)

    def _start(self):
        self.move(WX, WY)
        time.sleep(0.3)
        # GÉOMÉTRIE RÉELLE de ma fenêtre (le WM peut l'avoir déplacée) → ffmpeg filme
        # exactement là où elle est, pas une position théorique.
        gx, gy, gw, gh = WX, WY, WW, WH
        try:
            wid = subprocess.run(
                ["xdotool", "search", "--name", "JARVIS Capture"],
                env=ENV,
                capture_output=True,
                text=True,
            ).stdout.split()[-1]
            g = subprocess.run(
                ["xdotool", "getwindowgeometry", "--shell", wid],
                env=ENV,
                capture_output=True,
                text=True,
            ).stdout
            d = dict(l.split("=") for l in g.strip().splitlines() if "=" in l)
            gx, gy, gw, gh = int(d["X"]), int(d["Y"]), int(d["WIDTH"]), int(d["HEIGHT"])
            gw -= gw % 2
            gh -= gh % 2  # dimensions paires (yuv420p)
        except Exception:
            pass
        print(f"   fenêtre réelle → {gw}x{gh}+{gx}+{gy}", flush=True)
        # démarre ffmpeg puis le scroll, même t0
        self.ff = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "x11grab",
                "-framerate",
                "25",
                "-video_size",
                f"{gw}x{gh}",
                "-i",
                f"{DISP}+{gx},{gy}",
                "-t",
                f"{DUR + 0.5:.1f}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-pix_fmt",
                "yuv420p",
                SCREEN,
            ],
            env=ENV,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("🎥 capture + scroll JS…", flush=True)
        self.t0 = time.time()
        GLib.timeout_add(80, self._tick)  # ~12 fps de scroll = fluide
        return False

    def _frac(self, t):
        if t < T_INTRO:
            return 0.0
        if t < T_BAS:
            return (t - T_INTRO) / max(0.5, (T_BAS - T_INTRO))
        if t < T_REM:
            return 1.0
        return max(0.0, 1.0 - (t - T_REM) / max(0.5, (DUR - T_REM)))

    def _tick(self):
        t = time.time() - self.t0
        # garde le contenu vivant (compteurs) sans casser le scroll
        self._js("window.cdTick&&cdTick()")
        if int(t * 12) % 24 == 0:
            self._js("window.tick&&tick()")
        f = self._frac(t)
        # scroll absolu proportionnel à la hauteur réelle (recalculée à chaque tick)
        self._js(
            "(function(){var d=document.documentElement,b=document.body;"
            "var mx=Math.max(d.scrollHeight,b.scrollHeight)-window.innerHeight;"
            f"window.scrollTo(0, mx*{f:.4f});}})();"
        )
        if t >= DUR + 0.3:
            try:
                self.ff.wait(timeout=10)
            except Exception:
                try:
                    self.ff.terminate()
                except Exception:
                    pass
            GLib.idle_add(Gtk.main_quit)
            return False
        return True


# envoie les widgets-desktop existants HORS-CHAMP (systemd les relance, add,hidden
# ne tient pas) — ma fenêtre Cap est keep_above de toute façon.
sh(
    "bash",
    "-c",
    "wmctrl -l | awk '/JARVIS Planning Widget/{print $1}' | "
    "while read w; do wmctrl -i -r $w -e 0,3000,0,600,1000 2>/dev/null; done",
    capture_output=True,
)

win = Cap()
win.show_all()
Gtk.main()

# ── 3. mux ────────────────────────────────────────────────────────────
print("🎬 mux…", flush=True)
r = sh(
    "ffmpeg",
    "-y",
    "-hide_banner",
    "-loglevel",
    "error",
    "-i",
    SCREEN,
    "-i",
    NARR_MP3,
    "-c:v",
    "copy",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-shortest",
    FINAL,
)
if r.returncode == 0 and os.path.exists(FINAL):
    print(f"✓ prêt : {FINAL} ({os.path.getsize(FINAL) // 1024} Ko)", flush=True)
    subprocess.run(["cp", "-f", FINAL, f"{OUTDIR}/widget-bureau.mp4"])
else:
    print("✗ mux échec")
    sys.exit(1)
