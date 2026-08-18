#!/usr/bin/env python3
"""jarvis-widget-desktop.py — widget planning EMBARQUÉ sur le bureau (WebKitGTK).

Affiche le dashboard http://127.0.0.1:8899 dans une fenêtre sans bordure,
collée sur tous les bureaux, sous les fenêtres (comme un widget de bureau).
  Usage : jarvis-widget-desktop.py [URL] [W] [H]  (défaut 480x900, coin haut-droit)
"""

import re
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
for v in ("4.1", "4.0"):
    try:
        gi.require_version("WebKit2", v)
        break
    except ValueError:
        continue
from gi.repository import Gtk, WebKit2, Gdk, GLib  # noqa: E402

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8899/"
W = int(sys.argv[2]) if len(sys.argv) > 2 else 600
H = int(sys.argv[3]) if len(sys.argv) > 3 else 900
MARGIN = 16


REFRESH_DATA_SECONDS = 2  # mode intensif
REFRESH_COUNTDOWN = 1  # chaque seconde


class Widget(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_default_size(W, H)
        self.set_decorated(False)  # sans bordure
        self.set_skip_taskbar_hint(True)  # pas dans la barre des tâches
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)  # sous les fenêtres = widget bureau
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.stick()  # présent sur tous les bureaux
        self.set_accept_focus(False)
        self.set_title("JARVIS Planning Widget")
        wv = WebKit2.WebView()
        self.wv = wv
        self._tick_counter = 0
        wv.load_uri(URL)
        # recharge si le serveur n'était pas prêt au démarrage
        wv.connect(
            "load-failed",
            lambda *a: (
                GLib.timeout_add_seconds(3, lambda: (wv.load_uri(URL), False)[1]),
                True,
            )[1],
        )
        self.add(wv)
        self.connect("destroy", Gtk.main_quit)
        self.connect("realize", self._place)
        # La résolution change en cours de session (underscan TV, écran rebranché).
        # Sans ces rappels la fenêtre reste figée sur l'ancienne géométrie et
        # décroche du bord droit.
        scr0 = Gdk.Screen.get_default()
        if scr0 is not None:
            scr0.connect("size-changed", self._place)
            scr0.connect("monitors-changed", self._place)
        GLib.timeout_add_seconds(10, self._replacer_si_derive)
        # WebKit GÈLE setInterval quand la fenêtre est en arrière-plan (keep_below).
        # On pompe le rafraîchissement depuis Python (jamais throttlé) : cdTick()
        # chaque seconde, tick() toutes les 2s en mode intensif.
        GLib.timeout_add_seconds(REFRESH_COUNTDOWN, self._pump)

    def _call_js(self, code: str):
        try:
            self.wv.run_javascript(code, None, None, None)
        except Exception:
            try:
                self.wv.evaluate_javascript(code, -1, None, None, None, None, None)
            except Exception:
                pass

    def _pump(self):
        # compte à rebours chaque seconde
        self._call_js("window.cdTick&&cdTick()")

        # données toutes les REFRESH_DATA_SECONDS (2s)
        self._tick_counter = (self._tick_counter + 1) % REFRESH_DATA_SECONDS
        if self._tick_counter == 0:
            self._call_js("window.tick&&tick()")

        # force redraw pour contourner le throttling WebKitGTK
        self._force_redraw()

        return True  # relance le timer GLib

    def _force_redraw(self):
        try:
            alloc = self.wv.get_allocation()
            self.wv.queue_draw()
        except Exception:
            pass

    def _zone_visible(self):
        """Zone RÉELLEMENT affichée par l'écran primaire (w, h, x, y).

        Gdk.Screen ment sur ce poste (largeur gonflée -> fenêtre hors champ) et
        le framebuffer X reste plus grand que le viewport quand l'underscan TV
        est actif. xrandr donne le viewport réel : c'est lui qui fait foi.
        """
        try:
            sortie = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True, timeout=5
            ).stdout
            lignes = [ligne for ligne in sortie.splitlines() if " connected" in ligne]
            for ligne in sorted(lignes, key=lambda l: "primary" not in l):
                trouve = re.search(r"\b(\d+)x(\d+)\+(\d+)\+(\d+)\b", ligne)
                if trouve:
                    w, h, x, y = (int(v) for v in trouve.groups())
                    if w > 0 and h > 0:
                        return w, h, x, y
        except Exception:
            pass
        scr = Gdk.Screen.get_default()
        return scr.get_width(), scr.get_height(), 0, 0

    def _geometrie_cible(self):
        sw, sh, ox, oy = self._zone_visible()
        return (
            max(ox, ox + sw - W - MARGIN),  # x : collé au bord droit visible
            oy + MARGIN,  # y
            sh - 2 * MARGIN,  # hauteur : dock plein-hauteur
        )

    def _place(self, *_):
        # dock plein-hauteur collé au bord DROIT de l'écran VISIBLE.
        x, y, h = self._geometrie_cible()
        self.resize(W, h)
        self.move(x, y)
        self.set_keep_below(True)

    def _replacer_si_derive(self):
        """Filet de sécurité : certains WM ignorent le move initial, et la
        résolution peut changer sans émettre de signal exploitable."""
        x, y, h = self._geometrie_cible()
        if self.get_position() != (x, y) or self.get_size()[1] != h:
            self._place()
        return True


if __name__ == "__main__":
    w = Widget()
    w.show_all()
    Gtk.main()
