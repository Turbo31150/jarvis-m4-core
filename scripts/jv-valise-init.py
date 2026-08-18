#!/usr/bin/env python3
"""jv-valise-init — matérialise la « valise » isolée d'une unité (Phase D).

Pour une unité du registre : crée la config isolée ~/.config/jarvis/<dept>/<cible>/valise.env,
une DB dédiée db/<dept>/<unite>.db (schéma minimal), et un manifeste valise.json.
NE renomme PAS le container (compose-managed → se fait via le fichier compose, hors scope).
Idempotent. Usage: jv-valise-init.py <nom_cible> [<nom_cible> ...] | --all-dept <dept>
"""

import json
import sqlite3
import sys
import stat
from pathlib import Path

HOME = Path.home()
REG = HOME / "jarvis" / "orchestrator" / "jv_registry.json"
CONF_ROOT = HOME / ".config" / "jarvis"
DB_ROOT = HOME / "jarvis" / "db"


def materialize(u):
    dept, cible, unite = u["dept"], u["nom_cible"], u["nom_cible"].split("-", 2)[-1]
    conf_dir = CONF_ROOT / dept / cible
    conf_dir.mkdir(parents=True, exist_ok=True)
    db_dir = DB_ROOT / dept
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"{unite}.db"

    # 1. DB dédiée (schéma minimal isolé)
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS valise_meta(k TEXT PRIMARY KEY, v TEXT)")
    con.execute("INSERT OR REPLACE INTO valise_meta(k,v) VALUES(?,?)", ("unit", cible))
    con.execute("INSERT OR REPLACE INTO valise_meta(k,v) VALUES(?,?)", ("dept", dept))
    con.commit()
    con.close()

    # 2. config isolée valise.env
    env = conf_dir / "valise.env"
    env.write_text(
        f"# Valise {cible} — généré par jv-valise-init\n"
        f"JV_UNIT={cible}\n"
        f"JV_DEPT={dept}\n"
        f"JV_NAME_LEGACY={u['nom_actuel']}\n"
        f"JV_PORT={u.get('port') or ''}\n"
        f"JV_PORT_RANGE={u.get('plage', '')}\n"
        f"JV_NETWORK=jvnet-{dept}\n"
        f"JV_DB={db_path}\n"
        f"JV_HEALTH=/health\n"
        f"JV_CONFIG_DIR={conf_dir}\n"
    )
    env.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600

    # 3. manifeste
    man = conf_dir / "valise.json"
    man.write_text(
        json.dumps(
            {
                "unit": cible,
                "dept": dept,
                "legacy": u["nom_actuel"],
                "type": u["type"],
                "port": u.get("port"),
                "range": u.get("plage"),
                "network": f"jvnet-{dept}",
                "db": str(db_path),
                "config_dir": str(conf_dir),
                "health": "/health",
                "rename_pending": "via compose"
                if u["type"] == "docker"
                else "via systemd unit",
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return {"unit": cible, "db": str(db_path), "config": str(conf_dir)}


def main(argv):
    reg = json.loads(REG.read_text())
    units = reg["units"]
    if "--all-dept" in argv:
        d = argv[argv.index("--all-dept") + 1]
        targets = [u for u in units if u["dept"] == d]
    else:
        names = [a for a in argv if not a.startswith("--")]
        targets = [u for u in units if u["nom_cible"] in names]
    if not targets:
        print("aucune unité ciblée")
        return 1
    for u in targets:
        r = materialize(u)
        print(f"✓ valise {r['unit']:30} db={r['db']}")
    print(f"[jv-valise-init] {len(targets)} valise(s) matérialisée(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
