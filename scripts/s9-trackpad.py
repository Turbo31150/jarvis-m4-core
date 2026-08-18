#!/usr/bin/env python3
"""Téléphone Android → trackpad pour le PC (X11).

Plug-and-play : auto-détecte le device adb branché ET son écran tactile
(peu importe le modèle / le chemin /dev/input/eventX / la résolution).
Lit le tactile via `adb getevent`, pilote le curseur avec `xdotool`.
Glisse = déplacement relatif · tap court = clic gauche.

Usage:
  python3 s9-trackpad.py [SERIAL] [--gain 0.85] [--dev /dev/input/eventN] [--selftest]
"""

import subprocess
import sys
import os
import time

GAIN = 0.85  # sensibilité (normalisée par la résolution tactile)
BASE_RANGE = 4096  # référence (S9) — le gain est mis à l'échelle vs le max réel
TAP_MOVE = 90  # < ce déplacement (unités device) + court = clic
TAP_MS = 320
SCROLL_STEP = 70  # unités device par cran de molette (2 doigts)

SERIAL = None
DEV = None
args = sys.argv[1:]
if args and not args[0].startswith("--"):
    SERIAL = args[0]
if "--gain" in sys.argv:
    GAIN = float(sys.argv[sys.argv.index("--gain") + 1])
if "--dev" in sys.argv:
    DEV = sys.argv[sys.argv.index("--dev") + 1]


def adb(*a, ser=None):
    base = ["adb"] + (["-s", ser] if ser else [])
    return subprocess.run(base + list(a), capture_output=True, text=True)


def auto_serial():
    out = adb("devices").stdout.splitlines()
    for ln in out[1:]:
        p = ln.split()
        if len(p) >= 2 and p[1] == "device":
            return p[0]
    return None


def find_touch(ser):
    """Retourne (devpath, max_x, max_y) du 1er écran tactile (ABS_MT_POSITION_X)."""
    out = adb("shell", "getevent", "-lp", ser=ser).stdout.splitlines()
    cur = None
    dev = None
    mx = my = BASE_RANGE
    for ln in out:
        s = ln.strip()
        if s.startswith("add device"):
            cur = s.split(":")[-1].strip()
        elif "ABS_MT_POSITION_X" in s and cur:
            dev = cur
            for t in s.split():
                if t.isdigit():
                    pass
            if "max" in s:
                try:
                    mx = int(s.split("max")[1].split(",")[0])
                except:
                    pass
        elif "ABS_MT_POSITION_Y" in s and dev == cur and "max" in s:
            try:
                my = int(s.split("max")[1].split(",")[0])
            except:
                pass
        elif dev and cur != dev:
            break
    return dev, mx, my


def xdo(*a):
    subprocess.run(
        ["xdotool", *a],
        env={**os.environ, "DISPLAY": ":0"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def loc():
    r = subprocess.run(
        ["xdotool", "getmouselocation", "--shell"],
        env={**os.environ, "DISPLAY": ":0"},
        capture_output=True,
        text=True,
    )
    return r.stdout.strip().replace("\n", " ")


def _main():
    global SERIAL, DEV
    if "--selftest" in sys.argv:
        b = loc()
        for _ in range(20):
            xdo("mousemove_relative", "--", "8", "5")
        a = loc()
        print("[selftest] avant:", b)
        print("[selftest] apres:", a)
        print("[selftest] RESULT:", "OK (curseur bouge)" if b != a else "FAIL")
        sys.exit(0 if b != a else 1)

    if not SERIAL:
        SERIAL = auto_serial()
    if not SERIAL:
        print("[trackpad] aucun téléphone adb branché (adb devices vide).", flush=True)
        sys.exit(2)
    if not DEV:
        dev, maxx, maxy = find_touch(SERIAL)
    else:
        dev, maxx, maxy = DEV, BASE_RANGE, BASE_RANGE
    DEV = dev
    if not DEV:
        print(f"[trackpad] pas d'écran tactile trouvé sur {SERIAL}.", flush=True)
        sys.exit(3)

    # gain normalisé : même ressenti quelle que soit la résolution tactile
    eff = GAIN * (BASE_RANGE / max(maxx, 1))
    model = adb("shell", "getprop", "ro.product.model", ser=SERIAL).stdout.strip()
    print(
        f"[trackpad] actif — {model} ({SERIAL}) {DEV} max={maxx}x{maxy} gain_eff={eff:.2f}. "
        f"Touche l'écran du téléphone pour bouger le curseur du PC.",
        flush=True,
    )
    proc = subprocess.Popen(
        ["adb", "-s", SERIAL, "shell", "getevent", "-lt", DEV],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    process_events(proc.stdout, xdo, eff)


def process_events(
    lines,
    emit,
    eff,
    tap_move=TAP_MOVE,
    tap_ms=TAP_MS,
    scroll_step=SCROLL_STEP,
    clock=time.time,
):
    """Décode un flux `getevent -lt` (protocole B) en gestes trackpad.

    1 doigt  : glisse = curseur, tap court = clic gauche.
    2 doigts : glisse verticale = défilement, tap court = clic droit.
    `emit(*args)` reçoit les actions xdotool (mockable pour les tests).
    """
    cur_slot = 0
    track = {}  # slot -> tracking id (présent = doigt posé)
    pos = {}  # slot -> [x, y]

    prev_n = 0
    gmax = 0  # nb max de doigts vus dans le geste courant
    gstart = 0.0
    gmove = 0.0  # déplacement cumulé (unités device)
    did_scroll = False
    ppx = ppy = None  # dernière pos doigt primaire (curseur)
    spy = None  # dernière pos Y doigt primaire (défilement)
    acc_x = acc_y = 0.0
    scroll_acc = 0.0

    for line in lines:
        p = line.split()
        if len(p) < 2:
            continue
        tok = p[-2]
        val = p[-1]
        if tok == "ABS_MT_SLOT":
            try:
                cur_slot = int(val, 16)
            except Exception:
                cur_slot = 0
        elif tok == "ABS_MT_TRACKING_ID":
            if val.lower().startswith("f"):  # ffffffff = doigt levé
                track.pop(cur_slot, None)
                pos.pop(cur_slot, None)
            else:
                track[cur_slot] = val
        elif tok == "ABS_MT_POSITION_X":
            try:
                pos.setdefault(cur_slot, [None, None])[0] = int(val, 16)
            except Exception:
                pass
        elif tok == "ABS_MT_POSITION_Y":
            try:
                pos.setdefault(cur_slot, [None, None])[1] = int(val, 16)
            except Exception:
                pass
        elif "SYN_REPORT" in line:
            n = len(track)
            now = clock()
            if prev_n == 0 and n > 0:  # début d'un geste
                gstart = now
                gmax = n
                gmove = 0.0
                did_scroll = False
                ppx = ppy = spy = None
                acc_x = acc_y = scroll_acc = 0.0
            gmax = max(gmax, n)
            if prev_n > 0 and n == 0:  # fin du geste -> clic éventuel
                dt = (now - gstart) * 1000
                if gmax == 1 and gmove < tap_move and dt < tap_ms:
                    emit("click", "1")
                elif (
                    gmax == 2
                    and not did_scroll
                    and gmove < tap_move * 2
                    and dt < tap_ms
                ):
                    emit("click", "3")
                ppx = ppy = spy = None
            act = sorted(track.keys())
            if n == 1:
                xy = pos.get(act[0])
                if xy and xy[0] is not None and xy[1] is not None:
                    x, y = xy
                    if ppx is not None:
                        dx = x - ppx
                        dy = y - ppy
                        gmove += abs(dx) + abs(dy)
                        acc_x += dx * eff
                        acc_y += dy * eff
                        mx = int(acc_x)
                        my = int(acc_y)
                        if mx or my:
                            # PAS de --sync : contre un bord d'écran, --sync attend
                            # une cible jamais atteinte et fige le driver.
                            emit("mousemove_relative", "--", str(mx), str(my))
                            acc_x -= mx
                            acc_y -= my
                    ppx, ppy = x, y
                spy = None
            elif n == 2:
                xy = pos.get(act[0])
                if xy and xy[1] is not None:
                    y = xy[1]
                    if spy is not None:
                        dy = y - spy
                        gmove += abs(dy)
                        scroll_acc += dy
                        while scroll_acc >= scroll_step:
                            emit("click", "5")  # défilement bas
                            scroll_acc -= scroll_step
                            did_scroll = True
                        while scroll_acc <= -scroll_step:
                            emit("click", "4")  # défilement haut
                            scroll_acc += scroll_step
                            did_scroll = True
                    spy = y
                ppx = ppy = None
            prev_n = n


if __name__ == "__main__":
    _main()
