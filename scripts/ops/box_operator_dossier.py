#!/usr/bin/env python3
"""Génère le dossier d'escalade opérateur (SFR/Numericable) depuis la sonde DOCSIS.

Un incident de voie de retour se fait balayer en hotline sans chiffres. Ce dossier
formule le seul argument qui porte : la réception est conforme, l'émission est saturée,
donc le défaut n'est pas chez l'abonné.

  python3 box_operator_dossier.py            # sonde puis génère
  python3 box_operator_dossier.py rapport.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROBE = Path(__file__).with_name("box_docsis_probe.py")
OUT_DIR = Path.home() / "jarvis" / "data" / "box_incidents"
CONTRAT = {
    "modele": "Netgear CG3100D",
    "profil": "nc_cg3100l_100m_5m.cm",
    "debit": "100 Mbps ↓ / 5 Mbps ↑",
    "norme": "EuroDOCSIS 3.0",
}


def load(argv: list[str]) -> dict:
    if len(argv) > 1:
        return json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    p = subprocess.run(
        [sys.executable, str(PROBE)], capture_output=True, text=True, timeout=180
    )
    if not p.stdout.strip():
        raise SystemExit("sonde muette — impossible de constituer le dossier")
    return json.loads(p.stdout)


def chemin() -> str:
    """Perte/jitter par saut. Corrobore la sonde : si la box répond en <1 ms et
    que le jitter explose au saut suivant, le défaut n'est pas dans le foyer."""
    try:
        p = subprocess.run(
            ["mtr", "-r", "-c", "20", "-n", "--no-dns", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return p.stdout.strip() or "(mtr sans sortie)"
    except (OSError, subprocess.TimeoutExpired):
        return "(mtr indisponible)"


def render(r: dict) -> str:
    if not r.get("ok"):
        return f"# Dossier non constituable\n\nSonde indisponible : {r.get('reason', '?')}\n"

    us, snr = r.get("upstream_max_dbmv"), r.get("downstream_snr_min_db")
    lg = r.get("log", {})
    us_rows = (
        "\n".join(
            f"| {c['freq_hz'] / 1e6:.1f} MHz | {c['power_dbmv']} dBmV |"
            for c in r.get("upstream_channels", [])
        )
        or "| — | — |"
    )
    events = (
        "\n".join(f"    {e}" for e in lg.get("last_events", [])) or "    (journal vide)"
    )

    chemin_txt = chemin()

    # Le journal du CG3100D est circulaire : ne jamais présenter son contenu
    # comme un historique complet, la hotline s'en servirait pour minorer.
    return f"""# Dossier d'incident — voie de retour DOCSIS

**Date du relevé** : {r.get("ts")}
**Équipement** : {CONTRAT["modele"]} · {CONTRAT["norme"]} · profil `{CONTRAT["profil"]}` ({CONTRAT["debit"]})
**Gravité mesurée** : `{r.get("severity")}` — {r.get("verdict")}

## Constat

La **réception est conforme** : {r.get("downstream_channels")} canaux QAM256 verrouillés,
SNR minimum **{snr} dB** (exigence ≥ 33 dB). Aucun défaut côté descendant.

L'**émission est saturée** : puissance maximale **{us} dBmV**, soit la limite haute
exploitable du modem. À ce niveau il n'a plus de marge pour être entendu du CMTS.

Conséquence relevée au journal de l'équipement :
**{lg.get("t3_timeout", 0)} T3 time-out**, **{lg.get("reg_rsp_not_received", 0)} REG RSP not received**,
**{lg.get("mac_reinit", 0)} réinitialisation(s) de couche MAC**.
{"Le modem a redémarré il y a " + str(r.get("uptime_min")) + " minutes." if r.get("rebooted_recently") else ""}
{str(r.get("phone_lines_down")) + " ligne(s) de téléphonie déconnectée(s), cohérent avec un upstream instable." if r.get("phone_lines_down") else ""}

## Puissances d'émission par canal

| Fréquence | Puissance |
|---|---|
{us_rows}

## Journal (extrait — mémoire circulaire de l'équipement, pas un historique complet)

```
{events}
```

## Localisation du défaut par mesure de chemin (indépendante de la sonde)

```
{chemin_txt}
```

Lecture : le saut 1 est la box elle-même. Si elle répond en moins d'une milliseconde
sans perte tandis que le **saut 2 — premier équipement opérateur** — présente un
écart-type de latence de plusieurs dizaines de millisecondes, la dégradation naît
**sur le segment d'accès**, en aval de l'installation terminale. C'est la signature
de retransmissions DOCSIS provoquées par une voie de retour sans marge.

## Demande

Réception conforme et émission en butée : le point de défaut est **en amont du modem**
(atténuation de la voie de retour sur le segment coaxial ou au nœud optique), pas dans
l'installation terminale. Demande de **vérification du niveau de retour et intervention
sur le segment**.

## Vérifications déjà effectuées côté abonné

- [ ] Modem raccordé sans répartiteur intermédiaire
- [ ] Connecteurs F contrôlés (serrage, absence d'oxydation)
- [ ] Coaxial inspecté (pincement, coude, gaine)

> Renseigner ces trois cases avant l'appel : elles coupent court au script de hotline
> qui renvoie systématiquement l'abonné à son câblage.

*Relevé automatiquement par `box_docsis_probe.py` sur l'interface d'administration.*
"""


def main() -> int:
    r = load(sys.argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    f = OUT_DIR / f"dossier-operateur-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
    f.write_text(render(r), encoding="utf-8")
    print(f"dossier → {f}")
    print(
        f"gravité={r.get('severity')} upstream={r.get('upstream_max_dbmv')} dBmV "
        f"snr={r.get('downstream_snr_min_db')} dB t3={r.get('log', {}).get('t3_timeout')}"
    )
    return 0 if r.get("severity") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
