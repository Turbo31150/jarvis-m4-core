#!/usr/bin/env python3
"""jarvis-precharge — index unifie des ressources LOCALES executables (0 token).

Repond a un manque reel constate le 2026-08-18 : le parc expose 215 agents,
~1007 skills, 91 serveurs MCP, ~265 CLI, 47 slash-commands et 7 plugins, sans
aucun index commun. Les briques voisines ne couvrent PAS ce besoin :
  · skillmp.py        -> catalogue SkillsMP (218 372 skills du MARKETPLACE distant)
  · jarvis-router.py  -> routeur de sous-titres vocaux (subtitles/live.txt), pas d agents
  · jarvis-boot-sequencer -> simulation pure (0 appel systeme, 19 time.sleep) : NE RIEN EN ATTENDRE

Sous-commandes : build · search · stats · doctor

Tout est deterministe : SQLite + FTS5 (unicode61 remove_diacritics 2 pour que
"prechargement" trouve "préchargement"). Aucune inference, aucun reseau.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

HOME = Path.home()
DB = Path(os.environ.get("JARVIS_PRECHARGE_DB", HOME / "jarvis/databases/precharge.db"))

# Segments qui, dans une description, annoncent une liste de declencheurs.
_TRIGGER_RE = re.compile(
    r"(?:Triggers?(?:\s+FR/EN)?\s*(?:on|:|—|-)|"
    r"Use when(?:ever)?(?:\s+(?:the\s+)?user\s+(?:asks?|says?|wants?))?|"
    r"Utilise[rz]?\s+(?:cet\s+agent\s+)?(?:quand|lorsque)|"
    r"A declencher quand|Triggers)\b(.*)",
    re.IGNORECASE | re.DOTALL,
)
_MOT_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9_+-]{2,}")


def frontmatter(chemin: Path, max_lignes: int = 120) -> dict:
    """Parse le frontmatter YAML sans PyYAML. Tolerant : jamais d exception."""
    try:
        with chemin.open("r", encoding="utf-8", errors="replace") as f:
            premiere = f.readline()
            if premiere.strip() != "---":
                return {}
            corps = []
            for i, ligne in enumerate(f):
                if ligne.strip() == "---":
                    break
                if i > max_lignes:
                    break
                corps.append(ligne.rstrip("\n"))
    except OSError:
        return {}
    champs: dict[str, str] = {}
    cle = None
    for ligne in corps:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", ligne)
        if m:
            cle = m.group(1).strip()
            champs[cle] = m.group(2).strip()
        elif cle and ligne.strip():
            champs[cle] += " " + ligne.strip()
    for k, v in champs.items():
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        champs[k] = v
    return champs


def extrait_mots_cles(nom: str, description: str) -> str:
    """Mots-cles = nom eclate + segment de declencheurs, dedupe, borne."""
    mots: list[str] = []
    for part in re.split(r"[-_:./]", nom or ""):
        if len(part) >= 3:
            mots.append(part.lower())
    m = _TRIGGER_RE.search(description or "")
    if m:
        mots.extend(w.lower() for w in _MOT_RE.findall(m.group(1))[:60])
    vus, sortie = set(), []
    for w in mots:
        if w not in vus:
            vus.add(w)
            sortie.append(w)
    return " ".join(sortie[:80])


def entete_script(chemin: Path) -> str:
    """1re ligne de sens d un executable : docstring, ou commentaire de tete."""
    try:
        with chemin.open("r", encoding="utf-8", errors="replace") as f:
            lignes = [f.readline() for _ in range(12)]
    except (OSError, UnicodeDecodeError):
        return ""
    for i, l in enumerate(lignes):
        s = l.strip()
        if s.startswith(('"""', "'''")):
            texte = s.strip("\"'")
            if texte:
                return texte[:300]
            if i + 1 < len(lignes):
                return lignes[i + 1].strip()[:300]
        if s.startswith("#") and not s.startswith("#!") and len(s) > 4:
            return s.lstrip("# ").strip()[:300]
    return ""


def collecte() -> tuple[list[dict], list[str]]:
    """Rend (ressources, anomalies). Les anomalies sont REMONTEES, jamais avalees."""
    res: list[dict] = []
    anomalies: list[str] = []
    vus: dict[tuple, str] = {}

    def ajoute(type_, nom, chemin, description, commande="", etat="ok"):
        if not nom:
            return
        # Deux fichiers peuvent declarer le MEME name (ex. une skill locale et sa
        # copie de plugin). On garde la premiere et on remonte la collision :
        # l avaler silencieusement transformerait un doublon reel en index tronque.
        cle = (type_, nom)
        if cle in vus:
            anomalies.append(f"doublon {type_} '{nom}' : {chemin} (deja pris par {vus[cle]})")
            return
        vus[cle] = str(chemin)
        res.append({
            "type": type_, "nom": nom, "chemin": str(chemin),
            "description": (description or "")[:2000],
            "mots_cles": extrait_mots_cles(nom, description or ""),
            "commande": commande, "etat": etat,
        })

    # --- agents ---
    for base in (HOME / ".claude/agents", HOME / "jarvis/.claude/agents"):
        for f in sorted(base.glob("*.md")) if base.is_dir() else []:
            # Un fichier prefixe '_' est neutralise (_deprecated_, _disabled_, _INDEX_).
            # L indexer volait le nom a l agent actif : le tri alphabetique le faisait
            # passer EN PREMIER, donc gagner la deduplication. Bug reel du 18/08.
            if f.name.startswith("_"):
                continue
            fm = frontmatter(f)
            nom = fm.get("name") or f.stem
            if not fm.get("description"):
                anomalies.append(f"agent sans description : {f}")
            ajoute("agent", nom, f, fm.get("description", ""),
                   commande=f'Agent(subagent_type="{nom}")')

    # --- skills ---
    for base in (HOME / ".claude/skills", HOME / "jarvis/.claude/skills"):
        for d in sorted(base.iterdir()) if base.is_dir() else []:
            if not d.is_dir() or d.name.startswith("_"):
                continue
            sk = d / "SKILL.md"
            if not sk.is_file():
                anomalies.append(f"skill sans SKILL.md : {d}")
                continue
            fm = frontmatter(sk)
            # Le DOSSIER est l identifiant d invocation : m1-ace et ace sont deux
            # skills distinctes bien que m1-ace/SKILL.md declare name "ace".
            # Se fier au frontmatter fusionnait ~370 skills a tort.
            nom = d.name
            declare = fm.get("name", "")
            desc = fm.get("description", "")
            if declare and declare != nom:
                desc = f"(alias frontmatter : {declare}) {desc}"
            driver = d / "driver.sh"
            ajoute("skill", nom, sk, desc,
                   commande=(str(driver) if driver.is_file() else f"Skill({nom})"))

    # --- slash-commands ---
    for base in (HOME / ".claude/commands", HOME / "jarvis/.claude/commands"):
        for f in sorted(base.glob("*.md")) if base.is_dir() else []:
            fm = frontmatter(f)
            ajoute("commande", fm.get("name") or f.stem, f,
                   fm.get("description", ""), commande=f"/{f.stem}")

    # --- serveurs MCP (avec verification d existence : un serveur mort est signale) ---
    for cfg in (HOME / "jarvis/.mcp.json", HOME / ".claude.json"):
        if not cfg.is_file():
            continue
        try:
            data = json.loads(cfg.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError) as e:
            anomalies.append(f"config MCP illisible {cfg} : {e}")
            continue
        serveurs = data.get("mcpServers") or {}
        for nom, conf in serveurs.items():
            if not isinstance(conf, dict):
                continue
            cmd = conf.get("command") or conf.get("url") or ""
            args = conf.get("args") or []
            etat = "ok"
            cible = next((a for a in args if isinstance(a, str) and a.startswith("/")), None)
            if cible and not Path(cible).exists():
                etat = "cible_absente"
            desc = f"Serveur MCP {nom}. Transport {'http' if conf.get('url') else 'stdio'}. {cmd} {' '.join(map(str, args[:3]))}"
            ajoute("mcp", nom, cfg, desc, commande=str(cmd), etat=etat)

    # --- executables CLI ---
    for base in (HOME / ".local/bin", HOME / "jarvis/bin"):
        for f in sorted(base.iterdir()) if base.is_dir() else []:
            if not f.is_file() or not os.access(f, os.X_OK):
                continue
            if f.name.endswith((".bak", ".pyc")) or ".bak-" in f.name:
                continue
            etat = "ok"
            if f.is_symlink() and not f.resolve().exists():
                etat = "lien_casse"
                anomalies.append(f"lien symbolique casse : {f}")
            ajoute("cli", f.name, f, entete_script(f), commande=str(f), etat=etat)

    # --- conteneurs (via le wrapper obligatoire : docker local est bloque) ---
    wrapper = HOME / "jarvis/bin/jarvis-docker"
    if wrapper.is_file():
        import subprocess
        try:
            out = subprocess.run(
                [str(wrapper), "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
                capture_output=True, text=True, timeout=30)
            if out.returncode != 0:
                anomalies.append(f"jarvis-docker ps rc={out.returncode}: {out.stderr.strip()[:160]}")
            for ligne in out.stdout.strip().splitlines():
                bouts = ligne.split("\t")
                if len(bouts) < 2 or not bouts[0].strip():
                    continue
                nom, statut = bouts[0].strip(), bouts[1].strip()
                image = bouts[2].strip() if len(bouts) > 2 else ""
                ajoute("conteneur", nom, "tour:100.124.69.1",
                       f"Conteneur {nom} — {statut} — image {image}",
                       commande=f"{wrapper} logs --tail 50 {nom}",
                       etat="ok" if statut.startswith("Up") else "arrete")
        except Exception as e:
            anomalies.append(f"collecte conteneurs impossible ({type(e).__name__}: {e})")
    else:
        anomalies.append(f"wrapper absent : {wrapper} — conteneurs non collectes")

    # --- plugins ---
    base = HOME / ".claude/plugins"
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if not d.is_dir() or d.name in {"cache", "config", "data", "marketplaces", "quarantine"}:
            continue
        manifeste = next((m for m in (d / "plugin.json", d / ".claude-plugin/plugin.json") if m.is_file()), None)
        desc = ""
        if manifeste:
            try:
                desc = (json.loads(manifeste.read_text(encoding="utf-8", errors="replace")) or {}).get("description", "")
            except (json.JSONDecodeError, OSError):
                anomalies.append(f"manifeste plugin illisible : {manifeste}")
        ajoute("plugin", d.name, d, desc or f"Plugin local {d.name}")

    return res, anomalies


SCHEMA = """
CREATE TABLE IF NOT EXISTS ressources(
  id INTEGER PRIMARY KEY,
  type TEXT NOT NULL, nom TEXT NOT NULL, chemin TEXT,
  description TEXT, mots_cles TEXT, commande TEXT,
  etat TEXT DEFAULT 'ok', maj TEXT,
  UNIQUE(type, nom)
);
CREATE INDEX IF NOT EXISTS idx_res_type ON ressources(type);
CREATE INDEX IF NOT EXISTS idx_res_etat ON ressources(etat);
CREATE VIRTUAL TABLE IF NOT EXISTS ressources_fts USING fts5(
  nom, description, mots_cles,
  content='ressources', content_rowid='id',
  tokenize="unicode61 remove_diacritics 2"
);
CREATE TABLE IF NOT EXISTS builds(
  ts TEXT PRIMARY KEY, n_ressources INT, n_anomalies INT, duree_ms INT
);
"""


def ouvre() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(DB)
    cx.row_factory = sqlite3.Row
    cx.executescript("PRAGMA journal_mode=WAL;" + SCHEMA)
    return cx


def cmd_build(args) -> int:
    t0 = time.perf_counter()
    res, anomalies = collecte()
    if not res:
        print("ECHEC : 0 ressource collectee — rien n a ete ecrit.", file=sys.stderr)
        return 1
    cx = ouvre()
    maj = time.strftime("%Y-%m-%dT%H:%M:%S")
    with cx:
        # Reconstruction complete : une ressource supprimee du disque doit
        # disparaitre de l index (sinon l index ment par accumulation).
        cx.execute("DELETE FROM ressources")
        cx.executemany(
            "INSERT INTO ressources(type,nom,chemin,description,mots_cles,commande,etat,maj) "
            "VALUES(:type,:nom,:chemin,:description,:mots_cles,:commande,:etat,:maj)",
            [dict(r, maj=maj) for r in res],
        )
        cx.execute("INSERT INTO ressources_fts(ressources_fts) VALUES('rebuild')")
        cx.execute("INSERT OR REPLACE INTO builds VALUES(?,?,?,?)",
                   (maj, len(res), len(anomalies), int((time.perf_counter() - t0) * 1000)))
    par_type = dict(cx.execute("SELECT type, count(*) FROM ressources GROUP BY type ORDER BY 2 DESC"))
    print(f"index reconstruit : {len(res)} ressources en {int((time.perf_counter()-t0)*1000)} ms -> {DB}")
    for t, n in par_type.items():
        print(f"  {t:10} {n:5}")
    degrade = list(cx.execute("SELECT type, etat, count(*) c FROM ressources WHERE etat!='ok' GROUP BY 1,2"))
    if degrade:
        print("  -- entrees degradees (indexees mais signalees) --")
        for r in degrade:
            print(f"  {r['type']:10} {r['etat']:15} {r['c']}")
    if anomalies:
        print(f"  -- {len(anomalies)} anomalie(s), 10 premieres --")
        for a in anomalies[:10]:
            print(f"     {a}")
    return 0


def cmd_search(args) -> int:
    cx = ouvre()
    tokens = [t.lower() for t in _MOT_RE.findall(args.requete)]
    if not tokens:
        print("requete vide apres tokenisation", file=sys.stderr)
        return 2
    # OR-mode : le AND implicite de FTS5 effondre le rappel des le 2e mot.
    fts = " OR ".join(dict.fromkeys(tokens))
    sql = ("SELECT r.type, r.nom, r.commande, r.etat, "
           "substr(r.description,1,150) AS extrait, "
           "bm25(ressources_fts, 3.0, 1.0, 2.0) AS score "
           "FROM ressources_fts JOIN ressources r ON r.id = ressources_fts.rowid "
           "WHERE ressources_fts MATCH ? ")
    params: list = [fts]
    if args.type:
        sql += "AND r.type = ? "
        params.append(args.type)
    sql += "ORDER BY score LIMIT ?"
    params.append(args.limite)
    try:
        lignes = list(cx.execute(sql, params))
    except sqlite3.OperationalError as e:
        print(f"erreur FTS5 : {e}", file=sys.stderr)
        return 2
    if not lignes:
        print("aucun resultat")
        return 0
    if args.json:
        print(json.dumps([dict(l) for l in lignes], ensure_ascii=False, indent=2))
        return 0
    for l in lignes:
        drapeau = "" if l["etat"] == "ok" else f"  [!{l['etat']}]"
        print(f"[{l['type']:9}] {l['nom']:<42} {l['score']:7.2f}{drapeau}")
        if l["commande"]:
            print(f"            -> {l['commande']}")
        if l["extrait"]:
            print(f"            {l['extrait'].strip()[:130]}")
    return 0


def _age_h(chemin: Path) -> float | None:
    try:
        return (time.time() - chemin.stat().st_mtime) / 3600
    except OSError:
        return None


def cmd_stats(args) -> int:
    cx = ouvre()
    dernier = cx.execute("SELECT * FROM builds ORDER BY ts DESC LIMIT 1").fetchone()
    if not dernier:
        print("index jamais construit — lancer : jarvis-precharge build", file=sys.stderr)
        return 1
    print(f"dernier build : {dernier['ts']}  ({dernier['n_ressources']} ressources, "
          f"{dernier['n_anomalies']} anomalies, {dernier['duree_ms']} ms)")

    # Fraicheur du CORPUS, distincte de celle du build. Un index reconstruit il y a
    # 2 minutes sur un miroir vieux de 5 jours est perime : afficher la seule date
    # de build laisserait croire l'inverse.
    seuil = float(os.environ.get("SYNC_MAX_H", "6"))
    temoin = Path.home() / "m1-sync/bibliotheque-vivante/lib/BLOCS-INDEX.tsv"
    age = _age_h(temoin)
    if age is None:
        print(f"corpus miroir : ABSENT ({temoin}) — lancer : bloc sync")
    else:
        etat = "frais" if age < seuil else f"PERIME (seuil {seuil:g}h)"
        print(f"corpus miroir : {age:.1f} h — {etat}")
    bdd_bloc = Path.home() / ".claude/bibliotheque/bibliotheque.db"
    if bdd_bloc.is_file():
        try:
            cb = sqlite3.connect(f"file:{bdd_bloc}?mode=ro", uri=True)
            n = cb.execute("SELECT count(*) FROM blocs").fetchone()[0]
            cb.close()
            print(f"moteur bloc   : {n} entrees interrogeables (bloc <mots-cles>)")
        except sqlite3.Error as e:
            print(f"moteur bloc   : illisible ({e})")
    for r in cx.execute("SELECT type, count(*) n, sum(etat!='ok') degrade FROM ressources GROUP BY 1 ORDER BY 2 DESC"):
        suffixe = f"  ({r['degrade']} degradee(s))" if r["degrade"] else ""
        print(f"  {r['type']:10} {r['n']:5}{suffixe}")
    print(f"  {'TOTAL':10} {cx.execute('SELECT count(*) FROM ressources').fetchone()[0]:5}")
    return 0


def cmd_doctor(args) -> int:
    """Verifie que l index correspond encore au disque. Sort 1 s il a derive."""
    cx = ouvre()
    indexe = cx.execute("SELECT count(*) FROM ressources").fetchone()[0]
    if not indexe:
        print("index VIDE", file=sys.stderr)
        return 1
    disque, _ = collecte()
    ecart = len(disque) - indexe
    print(f"index={indexe}  disque={len(disque)}  ecart={ecart:+d}")
    manquants = list(cx.execute(
        "SELECT type, nom, chemin FROM ressources WHERE etat!='ok' LIMIT 15"))
    if manquants:
        print("entrees degradees :")
        for m in manquants:
            print(f"  [{m['type']}] {m['nom']} — {m['chemin']}")
    if ecart:
        print("=> l index a derive, relancer : jarvis-precharge build", file=sys.stderr)
        return 1
    print("=> index a jour")
    return 0



# --- pont vers le moteur `bloc` -------------------------------------------
# `bloc` (~/.claude/bin/bloc) est le moteur FTS5 deja cable au hook
# UserPromptSubmit. Il ingere tout *.tsv depose dans ~/.claude/bibliotheque/local/
# au schema a 5 colonnes. On ne duplique donc pas un second moteur de recherche :
# on alimente celui qui est deja en production.
LOCAL_BLOC = Path(os.environ.get("BLOC_LOCAL_DIR", HOME / ".claude/bibliotheque/local"))
ENTETE_TSV = "bloc_id\tsource\tmots_cles\taction\tdanger"
# vert = lecture/invocation · orange = peut modifier l etat de la machine
DANGER = {"agent": "🟢", "skill": "🟢", "commande": "🟢", "mcp": "🟢",
          "plugin": "🟢", "cli": "🟠", "conteneur": "🟠"}


def _propre(v: str) -> str:
    """Un TSV ne tolere ni tabulation ni saut de ligne dans une cellule."""
    return re.sub(r"\s+", " ", (v or "").replace("\t", " ")).strip()


def cmd_export(args) -> int:
    cx = ouvre()
    n_total = cx.execute("SELECT count(*) FROM ressources").fetchone()[0]
    if not n_total:
        print("index vide — lancer d abord : jarvis-precharge build", file=sys.stderr)
        return 1
    LOCAL_BLOC.mkdir(parents=True, exist_ok=True)
    types = [r[0] for r in cx.execute("SELECT DISTINCT type FROM ressources ORDER BY 1")]
    ecrits = 0
    for t in types:
        cible = LOCAL_BLOC / f"precharge-{t}s.tsv"
        lignes = [ENTETE_TSV]
        for r in cx.execute(
                "SELECT nom, description, mots_cles, commande, etat, chemin "
                "FROM ressources WHERE type=? ORDER BY nom", (t,)):
            # Les mots-cles portent le rappel : nom + declencheurs + type + etat,
            # pour que `bloc agent trading` ou `bloc conteneur arrete` fonctionnent.
            mots = _propre(f"{r['nom']} {r['mots_cles']} {t} {r['description'][:220]}")
            action = _propre(r["commande"] or r["chemin"])
            danger = DANGER.get(t, "🟠")
            if r["etat"] != "ok":
                danger = "🟠"
                mots = f"{mots} {r['etat']}"
            lignes.append("\t".join([
                _propre(f"precharge.{t}.{r['nom']}"), "precharge-m4",
                mots[:600], action[:300], danger,
            ]))
        cible.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        print(f"  {cible.name:28} {len(lignes)-1:5} entrees")
        ecrits += len(lignes) - 1
    print(f"{ecrits} entrees exportees vers {LOCAL_BLOC}")
    print("=> integrer a la recherche unifiee : ~/.claude/bin/bloc build")
    return 0



# --- controle de fraicheur de TOUT l ecosysteme ----------------------------
# Motif recurrent du parc (atomes du 17-18/08) : un composant meurt et PERSONNE
# ne le voit pendant des jours — board muet depuis le 13/08, openclaw arrete,
# outils portes de M1 qui se taisent sans lever d erreur. Un tableau de fraicheur
# ne vaut que s il couvre AUSSI ce qui n est pas un fichier : services, conteneurs,
# quorum Swarm, endpoints. Tout ce qui est mesure est date ou sonde ; rien n est
# declare "ok" par defaut.

def _sh(cmd: str, timeout: float = 12.0):
    import subprocess
    try:
        r = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 255, "", f"{type(e).__name__}: {e}"


def cmd_fraicheur(args) -> int:
    seuil = float(os.environ.get("SYNC_MAX_H", "6"))
    lignes: list[tuple[str, str, str]] = []   # (etat, domaine, detail)

    def dit(etat, domaine, detail):
        lignes.append((etat, domaine, detail))

    # 1. corpus fichiers
    for nom, chemin, plafond in (
        ("corpus miroir", Path.home() / "m1-sync/bibliotheque-vivante/lib/BLOCS-INDEX.tsv", seuil),
        ("index precharge", DB, 24.0),
        ("moteur bloc", Path.home() / ".claude/bibliotheque/bibliotheque.db", 24.0),
    ):
        a = _age_h(chemin)
        if a is None:
            dit("PANNE", nom, f"absent : {chemin}")
        else:
            dit("OK" if a < plafond else "PERIME", nom, f"{a:.1f} h (plafond {plafond:g} h)")

    # 2. volumes des corpus : une chute brutale est un incident, pas une mise a jour
    for nom, base, table in (
        ("board.db", Path.home() / "jarvis/databases/board.db", "chunks"),
        ("catalogue skillsmp", Path.home() / "jarvis/databases/jarvis_master.db", "skillsmp_skills"),
    ):
        try:
            c = sqlite3.connect(f"file:{base}?mode=ro", uri=True)
            n = c.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            c.close()
            dit("OK" if n else "PANNE", nom, f"{n} lignes ({table})")
        except sqlite3.Error as e:
            dit("PANNE", nom, str(e)[:90])

    # 3. TSV locaux perimes : ils alimentent `bloc`, un TSV fige fige l index
    local = Path.home() / ".claude/bibliotheque/local"
    vieux = sorted(((f.name, _age_h(f)) for f in local.glob("*.tsv")),
                   key=lambda x: -(x[1] or 0))
    perimes = [(n, a) for n, a in vieux if a and a > 168]      # > 7 jours
    if perimes:
        dit("PERIME", "TSV locaux", f"{len(perimes)} fichier(s) > 7 j, le plus vieux : "
                                    f"{perimes[0][0]} ({perimes[0][1]:.0f} h)")
    else:
        dit("OK", "TSV locaux", f"{len(vieux)} fichier(s), tous < 7 j")

    # 4. services systemd
    rc, out, _ = _sh("systemctl --user list-units --state=failed --no-legend --no-pager | wc -l")
    n_fail = int(out or 0) if rc == 0 else -1
    dit("OK" if n_fail == 0 else "PANNE", "services --user", f"{n_fail} en echec")
    for svc in ("tdai-sidecar", "jarvis-precharge.timer"):
        rc, out, _ = _sh(f"systemctl --user is-active {svc}", 8)
        dit("OK" if out == "active" else "PANNE", f"service {svc}", out or "inconnu")

    # 5. sidecar memoire : le seul juge est une reponse HTTP, pas l etat systemd
    rc, out, _ = _sh("curl -s --max-time 5 http://127.0.0.1:3250/health", 8)
    dit("OK" if '"ok"' in out else "PANNE", "memoire :3250", out[:70] or "muet")

    # 6. inference 0-token — un endpoint qui repond mais ne sert plus qu'un modele
    # sur cinq n'est PAS "ok" : mesure du 18/08, LM Studio a redemarre et n'a
    # recharge que qwen3.5-9b. Et une panne du primaire n'est une PANNE que si le
    # repli est mort lui aussi : sinon la cascade tient, c'est un DEGRADE.
    def _n_modeles(url: str, cle: str) -> int:
        rc, out, _ = _sh(f"curl -s --max-time 8 {url}", 12)
        try:
            return len(json.loads(out).get(cle) or [])
        except Exception:
            return -1
    n_lms = _n_modeles("http://10.42.0.230:1234/v1/models", "data")
    n_oll = _n_modeles("http://127.0.0.1:11434/api/tags", "models")
    if n_lms > 1:
        dit("OK", "inference LM Studio", f"{n_lms} modeles servis")
    elif n_lms >= 0:
        dit("PERIME", "inference LM Studio", f"{n_lms} modele(s) seulement — rechargement partiel")
    elif n_oll > 0:
        dit("PERIME", "inference LM Studio", f"injoignable — repli Ollama actif ({n_oll} modeles)")
    else:
        dit("PANNE", "inference", "LM Studio ET Ollama muets — cascade 0-token rompue")
    dit("OK" if n_oll > 0 else "PANNE", "repli Ollama M4", f"{n_oll} modeles" if n_oll >= 0 else "muet")

    # 7. conteneurs + quorum Swarm (via le wrapper : docker local est bloque)
    w = Path.home() / "jarvis/bin/jarvis-docker"
    rc, out, err = _sh(f"{w} ps --format '{{{{.Status}}}}'", 25)
    if rc == 0:
        st = [l for l in out.splitlines() if l.strip()]
        up = sum(1 for l in st if l.startswith("Up"))
        dit("OK" if up == len(st) and st else "PANNE", "conteneurs", f"{up}/{len(st)} Up")
    else:
        dit("PANNE", "conteneurs", (err or "wrapper injoignable")[:90])
    rc, out, err = _sh(f"{w} node ls --format '{{{{.Hostname}}}} {{{{.Status}}}}'", 25)
    if rc == 0:
        dit("OK", "quorum Swarm", f"{len(out.splitlines())} noeud(s)")
    else:
        court = "SANS LEADER (quorum raft perdu)" if "leader" in (err or "").lower() else (err or "?")[:80]
        dit("PANNE", "quorum Swarm", court)

    largeur = max(len(d) for _, d, _ in lignes)
    icone = {"OK": "✅", "PERIME": "⚠️ ", "PANNE": "❌"}
    for etat, domaine, detail in lignes:
        print(f"{icone[etat]} {domaine:<{largeur}}  {detail}")
    n_p = sum(1 for e, _, _ in lignes if e == "PANNE")
    n_v = sum(1 for e, _, _ in lignes if e == "PERIME")
    print(f"\nRESUME : {len(lignes)-n_p-n_v} OK · {n_v} perime(s) · {n_p} panne(s)")
    return 1 if n_p else 0


def main() -> int:
    p = argparse.ArgumentParser(prog="jarvis-precharge", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("build", help="(re)construit l index depuis le disque")
    ps = sp.add_parser("search", help="recherche FTS5 0-token")
    ps.add_argument("requete")
    ps.add_argument("--type", choices=["agent", "skill", "commande", "mcp", "cli", "plugin"])
    ps.add_argument("--limite", type=int, default=12)
    ps.add_argument("--json", action="store_true")
    sp.add_parser("export", help="ecrit les TSV pour le moteur `bloc`")
    sp.add_parser("stats", help="etat de l index")
    sp.add_parser("doctor", help="detecte la derive index/disque")
    sp.add_parser("fraicheur", help="controle de fraicheur de TOUT l ecosysteme")
    args = p.parse_args()
    return {"build": cmd_build, "search": cmd_search, "export": cmd_export,
            "stats": cmd_stats, "doctor": cmd_doctor,
            "fraicheur": cmd_fraicheur}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
