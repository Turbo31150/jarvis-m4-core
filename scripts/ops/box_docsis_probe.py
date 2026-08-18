#!/usr/bin/env python3
"""Sonde DOCSIS de la box Numericable CG3100D (192.168.0.1) — 0 token.

Pilote le Chromium du container jarvis-browseros (:9108, endpoint /chromium/function)
parce que le firmware de la box reset tout POST qui ne vient pas d'un vrai navigateur.

Relève : uptime (révèle les reboots), SNR + puissance downstream, puissance upstream
(le vrai point de rupture), rafales de T3 time-out dans le journal, état des lignes.

Sortie JSON sur stdout + code retour = niveau de gravité, pour chaîner un domino :
  0 = OK        1 = dégradé (upstream haut OU T3 récents)      2 = incident (reboot + T3)
  3 = sonde inutilisable (box ou navigateur injoignable) — surtout PAS un faux "OK"
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone

BOX = "192.168.0.1"
BROWSERLESS = "http://127.0.0.1:9108/chromium/function"
PAGE_SIGNAL = "Numreseau_pa3_frequencecable.asp"
PAGE_LOGS = "Numreseau_pa4_logs.asp"

# Seuils DOCSIS. L'upstream est le discriminant : au-delà de 48 dBmV le modem
# n'a plus de marge d'émission et le CMTS finit par ne plus répondre au ranging.
US_WARN = 46.0
US_CRIT = 48.0
DS_SNR_MIN = 33.0
UPTIME_REBOOT_MIN = 30  # uptime < 30 min => la box a redémarré récemment

# Le login est conditionnel : la session reste ouverte entre deux appels et le
# formulaire disparaît alors — un page.type() inconditionnel plante ("No element found").
JS = """
export default async function ({ page }) {
  await page.authenticate({ username: 'admin', password: 'password' });
  const out = {};
  await page.goto('http://%(box)s/Numconfig.asp', { waitUntil: 'domcontentloaded', timeout: 25000 });
  if (await page.$('#identifiant')) {
    await page.type('#identifiant', 'admin');
    await page.type('#password', 'password');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 25000 }).catch(() => null),
      page.click('#envoyer'),
    ]);
  }
  out.dashboard = await page.evaluate(() => document.body.innerText);
  await page.goto('http://%(box)s/%(sig)s', { waitUntil: 'domcontentloaded', timeout: 25000 });
  out.signal = await page.evaluate(() => document.body.innerText);
  await page.goto('http://%(box)s/%(log)s', { waitUntil: 'domcontentloaded', timeout: 25000 });
  out.logs = await page.evaluate(() => document.body.innerText);
  return { data: out, type: 'application/json' };
}
""" % {"box": BOX, "sig": PAGE_SIGNAL, "log": PAGE_LOGS}


def scrape() -> dict | None:
    """Récupère les 3 pages via le navigateur piloté. None si la sonde est aveugle."""
    try:
        p = subprocess.run(
            [
                "curl",
                "-s",
                "--max-time",
                "90",
                "-X",
                "POST",
                "-H",
                "Content-Type: application/javascript",
                "--data-binary",
                "@-",
                BROWSERLESS,
            ],
            input=JS,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if p.returncode != 0 or not p.stdout.strip():
        return None
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        return None  # browserless renvoie l'erreur Puppeteer en texte brut
    d = d.get("data", d)
    return d if isinstance(d, dict) and "signal" in d else None


def parse_uptime(dashboard: str) -> int | None:
    """Uptime en minutes. Le firmware écrit les jours via document.write() → souvent absent."""
    m = re.search(
        r"(\d+)\s*j\w*[^\d]{0,12}(\d{1,3})h\D{1,3}(\d{1,2})m", dashboard, re.I
    )
    if m:
        d, h, mi = (int(x) for x in m.groups())
        return d * 1440 + h * 60 + mi
    m = re.search(r"(\d{1,3})h\s*:?\s*(\d{1,2})m", dashboard)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return None


def parse_channels(signal: str) -> tuple[list[dict], list[dict]]:
    """Sépare réception et émission : les deux tables ont un format de ligne distinct."""
    i = signal.find("Canal d'émission")
    ds_txt, us_txt = (signal[:i], signal[i:]) if i > -1 else (signal, "")

    # downstream : ... <freq> Hz <power> dBmV <snr> dBmV
    ds = [
        {"freq_hz": int(f), "power_dbmv": float(p), "snr_db": float(s)}
        for f, p, s in re.findall(
            r"(\d{7,10})\s*Hz\s+(-?[\d.]+)\s*dBmV\s+(-?[\d.]+)\s*dBmV", ds_txt
        )
        if int(f) > 0
    ]
    # upstream : ... <freq> Hz <power> dBmV  (pas de SNR remonté par ce firmware)
    us = [
        {"freq_hz": int(f), "power_dbmv": float(p)}
        for f, p in re.findall(
            r"(\d{7,10})\s*Hz\s+(-?[\d.]+)\s*dBmV(?!\s+-?[\d.]+\s*dBmV)", us_txt
        )
        if int(f) > 0
    ]
    return ds, us


def parse_log(logs: str) -> dict:
    """Compte les signatures d'instabilité. Le journal est circulaire : pas d'historique long."""
    return {
        "t3_timeout": len(re.findall(r"T3 time-?out", logs, re.I)),
        "reg_rsp_not_received": len(re.findall(r"REG RSP not received", logs, re.I)),
        "mac_reinit": len(re.findall(r"Re-initializing MAC", logs, re.I)),
        "last_events": [
            re.sub(r"\s+", " ", ln).strip()
            for ln in logs.splitlines()
            if re.search(
                r"T3 time-?out|REG RSP|Re-initializing MAC|startup error", ln, re.I
            )
        ][:8],
    }


def build() -> tuple[dict, int]:
    raw = scrape()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if raw is None:
        return {
            "ts": now,
            "ok": False,
            "severity": "probe_failed",
            "reason": "box ou Chromium :9108 injoignable — mesures indisponibles",
        }, 3

    ds, us = parse_channels(raw["signal"])
    if not ds or not us:
        # Une page signal vide/tronquée (déconnexion en cours de scrape) rend 0
        # canal des deux côtés ou d'un seul : ce n'est pas une "voie de retour
        # nominale", c'est une lecture inexploitable. La rapporter 'ok'/'nominale'
        # ferait croire à tort que l'accès est sain (invariant central : une sonde
        # aveugle n'est JAMAIS 'ok').
        return {
            "ts": now,
            "ok": False,
            "severity": "probe_failed",
            "reason": (
                f"page signal vide ou tronquée : {len(ds)} canal downstream, "
                f"{len(us)} canal upstream extrait(s) — mesures indisponibles"
            ),
        }, 3

    log = parse_log(raw["logs"])
    uptime = parse_uptime(raw["dashboard"])
    lines_down = len(
        re.findall(r"Ligne\s*\d\s*:\s*D[ée]connect", raw["dashboard"], re.I)
    )

    us_max = max((c["power_dbmv"] for c in us), default=None)
    snr_min = min((c["snr_db"] for c in ds), default=None)
    rebooted = uptime is not None and uptime < UPTIME_REBOOT_MIN

    reasons = []
    if us_max is not None and us_max >= US_CRIT:
        reasons.append(
            f"upstream {us_max} dBmV >= {US_CRIT} (plus de marge d'émission)"
        )
    elif us_max is not None and us_max >= US_WARN:
        reasons.append(f"upstream {us_max} dBmV >= {US_WARN} (marge faible)")
    if snr_min is not None and snr_min < DS_SNR_MIN:
        reasons.append(f"SNR downstream {snr_min} dB < {DS_SNR_MIN}")
    if log["t3_timeout"]:
        reasons.append(f"{log['t3_timeout']} T3 time-out au journal")
    if log["mac_reinit"]:
        reasons.append(f"{log['mac_reinit']} réinitialisation(s) MAC")
    if rebooted:
        reasons.append(f"reboot box il y a {uptime} min")

    # Un reboot conjugué à des T3 = incident actif, pas une simple dégradation.
    if rebooted and log["t3_timeout"]:
        sev, code = "incident", 2
    elif reasons:
        sev, code = "degraded", 1
    else:
        sev, code = "ok", 0

    return {
        "ts": now,
        "ok": True,
        "severity": sev,
        "reasons": reasons,
        "uptime_min": uptime,
        "rebooted_recently": rebooted,
        "upstream_max_dbmv": us_max,
        "upstream_channels": us,
        "downstream_snr_min_db": snr_min,
        "downstream_channels": len(ds),
        "phone_lines_down": lines_down,
        "log": log,
        "verdict": (
            "voie de retour saturée — dossier opérateur"
            if us_max is not None and us_max >= US_CRIT
            else "liaison nominale"
            if sev == "ok"
            else "à surveiller"
        ),
    }, code


if __name__ == "__main__":
    report, rc = build()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(rc)
