"""Module d'automatisations dynamiques pour l'app enseignante Pousseline.
Mails parents adaptatifs + suggestions de planning + log historique.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from flask import jsonify, request

import ai_local

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")

# ---------------------------------------------------------------------------
# Helpers SQL
# ---------------------------------------------------------------------------


def _get_conn():
    conn = sqlite3.connect(ECOLE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_table(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS automation_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            type       TEXT NOT NULL,
            cible      TEXT,
            contenu    TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )"""
    )
    conn.commit()


def _log(conn, type_, cible, contenu):
    conn.execute(
        "INSERT INTO automation_log(type, cible, contenu) VALUES (?, ?, ?)",
        (type_, cible, contenu),
    )
    conn.commit()


def _table_exists(conn, name):
    r = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return bool(r)


# ---------------------------------------------------------------------------
# Fallbacks modèles (si IA indispo)
# ---------------------------------------------------------------------------

_MAIL_FALLBACKS = {
    "absence": {
        "objet": "Absence de votre enfant",
        "corps": (
            "Bonjour,\n\nNous avons noté l'absence de {prenom} lors de la journée du {date}. "
            "Merci de nous transmettre un justificatif à votre retour.\n\n"
            "Cordialement,\nL'équipe enseignante"
        ),
    },
    "felicitations": {
        "objet": "Félicitations pour {prenom}",
        "corps": (
            "Bonjour,\n\nNous tenons à partager de bonnes nouvelles concernant {prenom} : "
            "votre enfant a fait preuve d'excellents progrès cette semaine. Bravo !\n\n"
            "Cordialement,\nL'équipe enseignante"
        ),
    },
    "inquietude": {
        "objet": "Point sur la situation de {prenom}",
        "corps": (
            "Bonjour,\n\nNous souhaitons vous informer de quelques difficultés rencontrées "
            "par {prenom} en classe. Seriez-vous disponible pour un échange ?\n\n"
            "Cordialement,\nL'équipe enseignante"
        ),
    },
    "rappel_sortie": {
        "objet": "Rappel : sortie scolaire à venir",
        "corps": (
            "Bonjour,\n\nNous vous rappelons qu'une sortie scolaire est prévue prochainement. "
            "Merci de vérifier l'autorisation et les modalités transmises précédemment.\n\n"
            "Cordialement,\nL'équipe enseignante"
        ),
    },
    "bilan_periode": {
        "objet": "Bilan de période pour {prenom}",
        "corps": (
            "Bonjour,\n\nVoici un bilan de la période écoulée pour {prenom}. "
            "N'hésitez pas à nous contacter pour tout complément d'information.\n\n"
            "Cordialement,\nL'équipe enseignante"
        ),
    },
}


def _apply_fallback(type_, prenom):
    tpl = _MAIL_FALLBACKS.get(type_, _MAIL_FALLBACKS["absence"])
    today = date.today().strftime("%d/%m/%Y")
    return {
        "objet": tpl["objet"].format(prenom=prenom, date=today),
        "corps": tpl["corps"].format(prenom=prenom, date=today),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _collect_suggestions():
    """Construit la liste des suggestions (sans Flask) — réutilisable par l'exécuteur autonome."""
    suggestions = []
    conn = _get_conn()
    _init_table(conn)
    if True:
        # --- Absences récentes (7 derniers jours) ---
        if _table_exists(conn, "presence") and _table_exists(conn, "eleves"):
            limit_date = (date.today() - timedelta(days=7)).isoformat()
            absents = conn.execute(
                """
                SELECT e.id, e.prenom, e.nom, p.date
                FROM presence p
                JOIN eleves e ON e.id = p.eleve_id
                WHERE p.present = 0 AND p.date >= ?
                ORDER BY p.date DESC
                """,
                (limit_date,),
            ).fetchall()
            seen = set()
            for row in absents:
                key = row["id"]
                if key not in seen:
                    seen.add(key)
                    suggestions.append(
                        {
                            "type": "mail_absence",
                            "titre": f"Mail d'absence : {row['prenom']} {row['nom']}",
                            "cible": f"{row['prenom']} {row['nom']}",
                            "raison": f"Absent(e) le {row['date']}",
                            "eleve_id": row["id"],
                        }
                    )

        # --- Élèves avec besoins particuliers sans mail récent ---
        if _table_exists(conn, "eleves"):
            besoins_eleves = conn.execute(
                "SELECT id, prenom, nom, besoins FROM eleves WHERE besoins IS NOT NULL AND besoins != ''",
            ).fetchall()
            # Vérifier si un bilan a été loggué récemment
            logged_cibles = set()
            if _table_exists(conn, "automation_log"):
                recents = conn.execute(
                    "SELECT cible FROM automation_log WHERE type='bilan_periode' AND date(created_at) >= date('now','-30 days')",
                ).fetchall()
                logged_cibles = {r["cible"] for r in recents}

            for eleve in besoins_eleves:
                nom_complet = f"{eleve['prenom']} {eleve['nom']}"
                if nom_complet not in logged_cibles:
                    suggestions.append(
                        {
                            "type": "bilan_periode",
                            "titre": f"Bilan à envoyer aux parents de {eleve['prenom']}",
                            "cible": nom_complet,
                            "raison": f"Besoins particuliers : {eleve['besoins']}",
                            "eleve_id": eleve["id"],
                        }
                    )

        # --- Sorties imminentes (≤ 14 jours, non annulées) → préparer mot parents ---
        if _table_exists(conn, "sorties"):
            sorties = conn.execute(
                """
                SELECT id, titre, date, statut FROM sorties
                WHERE statut != 'annulee'
                  AND date(date) BETWEEN date('now') AND date('now','+14 days')
                ORDER BY date
                """,
            ).fetchall()
            for s in sorties:
                suggestions.append(
                    {
                        "type": "rappel_sortie",
                        "titre": f"Sortie « {s['titre']} » le {s['date']}",
                        "cible": s["titre"],
                        "raison": "Préparer le mot aux parents / vérifier les autorisations",
                        "sortie_id": s["id"],
                    }
                )

        # --- Réunions à venir (≤ 14 jours) → préparer l'ordre du jour ---
        if _table_exists(conn, "reunions"):
            reunions = conn.execute(
                """
                SELECT id, titre, date, ordre_du_jour FROM reunions
                WHERE date(date) BETWEEN date('now') AND date('now','+14 days')
                ORDER BY date
                """,
            ).fetchall()
            for r in reunions:
                if not (r["ordre_du_jour"] or "").strip():
                    suggestions.append(
                        {
                            "type": "reunion",
                            "titre": f"Réunion « {r['titre']} » le {r['date']}",
                            "cible": r["titre"],
                            "raison": "Ordre du jour vide — à préparer",
                            "reunion_id": r["id"],
                        }
                    )

        # --- Élèves en difficulté (moyenne < 50%) → exercice à différencier ---
        if _table_exists(conn, "evaluations") and _table_exists(conn, "eleves"):
            faibles = conn.execute(
                """
                SELECT e.id, e.prenom, e.nom,
                       AVG(ev.note * 1.0 / NULLIF(ev.sur,0)) AS ratio,
                       COUNT(*) AS n
                FROM evaluations ev
                JOIN eleves e ON e.id = ev.eleve_id
                GROUP BY ev.eleve_id
                HAVING n >= 2 AND ratio IS NOT NULL AND ratio < 0.5
                ORDER BY ratio
                """,
            ).fetchall()
            for f in faibles:
                suggestions.append(
                    {
                        "type": "exercice_differencier",
                        "titre": f"Exercice adapté pour {f['prenom']}",
                        "cible": f"{f['prenom']} {f['nom']}",
                        "raison": f"Moyenne {round(f['ratio'] * 100)}% sur {f['n']} évals — différenciation conseillée",
                        "eleve_id": f["id"],
                    }
                )

    conn.close()
    return suggestions


def _route_suggestions():
    """Analyse les données réelles et propose des actions automatiques."""
    try:
        suggestions = _collect_suggestions()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"suggestions": suggestions, "total": len(suggestions)})


def _route_mail_dynamique():
    """Génère un mail parents dynamique via IA, loggue dans automation_log."""
    data = request.get_json(force=True, silent=True) or {}
    type_mail = data.get("type", "absence")
    eleve_id = data.get("eleve_id")
    contexte = data.get("contexte", "")

    prenom = "l'élève"
    nom = ""
    besoins = ""
    niveau = ""

    try:
        conn = _get_conn()
        _init_table(conn)

        if eleve_id and _table_exists(conn, "eleves"):
            row = conn.execute(
                "SELECT prenom, nom, besoins, niveau FROM eleves WHERE id = ?",
                (int(eleve_id),),
            ).fetchone()
            if row:
                prenom = row["prenom"] or prenom
                nom = row["nom"] or ""
                besoins = row["besoins"] or ""
                niveau = row["niveau"] or ""
    except Exception as e:
        return jsonify({"error": f"Erreur lecture élève : {e}"}), 500

    # Construire le prompt IA
    type_labels = {
        "absence": "un mail de suivi d'absence",
        "felicitations": "un mail de félicitations",
        "inquietude": "un mail exprimant une inquiétude bienveillante",
        "rappel_sortie": "un mail de rappel pour une sortie scolaire",
        "bilan_periode": "un bilan de période synthétique",
    }
    label = type_labels.get(type_mail, "un mail aux parents")
    infos_eleve = f"Prénom : {prenom}"
    if nom:
        infos_eleve += f", Nom : {nom}"
    if niveau:
        infos_eleve += f", Niveau : {niveau}"
    if besoins:
        infos_eleve += f", Besoins particuliers : {besoins}"
    if contexte:
        infos_eleve += f". Contexte supplémentaire : {contexte}"

    system = (
        "Tu es une enseignante bienveillante du primaire en France. "
        "Tu rédiges des mails professionnels et chaleureux pour les parents d'élèves. "
        "Réponds UNIQUEMENT avec un JSON valide de la forme : "
        '{"objet": "...", "corps": "..."} — pas de markdown, pas de commentaires.'
    )
    user = (
        f"Rédige {label} pour les parents. Infos élève : {infos_eleve}. "
        "Sois concis, bienveillant, professionnel. Utilise le prénom de l'élève dans le mail."
    )

    mail_data = None
    try:
        result = ai_local.generate(
            user=user, system=system, max_tokens=600, cache=False
        )
        import json

        text = result["text"].strip()
        # Nettoyer éventuels blocs markdown
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        mail_data = json.loads(text)
    except ai_local.AIUnavailable:
        mail_data = _apply_fallback(type_mail, prenom)
    except Exception:
        mail_data = _apply_fallback(type_mail, prenom)

    # Fallback si JSON incomplet
    if not isinstance(mail_data, dict) or "objet" not in mail_data:
        mail_data = _apply_fallback(type_mail, prenom)

    # Logger dans automation_log
    try:
        import json as _json

        _log(
            conn,
            type_mail,
            f"{prenom} {nom}".strip(),
            _json.dumps(mail_data, ensure_ascii=False),
        )
        conn.close()
    except Exception:
        pass

    return jsonify(mail_data)


def _route_planning_auto():
    """Génère une proposition de planning hebdomadaire via IA."""
    data = request.get_json(force=True, silent=True) or {}
    contraintes = data.get("contraintes", "")

    edt_json = ""
    try:
        conn = _get_conn()
        _init_table(conn)
        if _table_exists(conn, "kv"):
            row = conn.execute("SELECT v FROM kv WHERE k = 'edt'").fetchone()
            if row:
                edt_json = row["v"]
        conn.close()
    except Exception:
        pass

    system = (
        "Tu es une enseignante experte en organisation pédagogique du primaire en France. "
        "Tu proposes des plannings hebdomadaires équilibrés, adaptés aux rythmes des élèves."
    )
    edt_info = (
        f"Emploi du temps actuel (JSON) : {edt_json}"
        if edt_json
        else "Aucun emploi du temps enregistré."
    )
    contraintes_info = (
        f"Contraintes supplémentaires : {contraintes}" if contraintes else ""
    )

    user = (
        f"{edt_info}\n{contraintes_info}\n\n"
        "Propose un planning de la semaine équilibré : répartition des matières, "
        "alternance activités calmes/dynamiques, respect des temps de récréation. "
        "Présente le planning de façon lisible (lundi à vendredi, matin/après-midi)."
    )

    try:
        result = ai_local.generate(
            user=user, system=system, max_tokens=1000, cache=False
        )
        return jsonify({"texte": result["text"], "backend": result.get("backend", "")})
    except ai_local.AIUnavailable:
        return jsonify(
            {
                "texte": (
                    "Planning suggéré (modèle de base) :\n"
                    "Lundi : Français matin / Maths après-midi\n"
                    "Mardi : Maths matin / Arts / EPS après-midi\n"
                    "Mercredi : Découverte du monde / Lecture\n"
                    "Jeudi : Français matin / Sciences après-midi\n"
                    "Vendredi : Révisions / Projets créatifs"
                ),
                "backend": "fallback",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _route_log():
    """Retourne les 50 derniers éléments de automation_log."""
    try:
        conn = _get_conn()
        _init_table(conn)
        rows = conn.execute(
            "SELECT id, type, cible, contenu, created_at FROM automation_log ORDER BY id DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Exécuteur AUTONOME (planificateur on-demand, anti-surchauffe)
# ---------------------------------------------------------------------------

# Plafond thermique : au-dessus, on NE lance PAS d'inférence (évite la boucle 95°C).
_TEMP_MAX = 86
_MAIL_TYPES = {
    "mail_absence": "absence",
    "bilan_periode": "bilan_periode",
    "rappel_sortie": "rappel_sortie",
}


def _cpu_temp():
    """Température max des zones thermiques (°C). 0 si illisible."""
    import glob

    t = 0
    for p in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            with open(p) as f:
                t = max(t, int(f.read().strip()) // 1000)
        except Exception:
            pass
    return t


def _kv_get(conn, k, default=""):
    try:
        r = conn.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return r["v"] if r and r["v"] is not None else default
    except Exception:
        return default


def _build_mail(conn, type_, eleve_id):
    """Génère {objet,corps} pour un élève via IA, fallback modèle. Sans Flask."""
    prenom, nom, besoins, niveau = "l'élève", "", "", ""
    if eleve_id and _table_exists(conn, "eleves"):
        row = conn.execute(
            "SELECT prenom,nom,besoins,niveau FROM eleves WHERE id=?", (int(eleve_id),)
        ).fetchone()
        if row:
            prenom = row["prenom"] or prenom
            nom = row["nom"] or ""
            besoins = row["besoins"] or ""
            niveau = row["niveau"] or ""
    system = (
        "Tu es une enseignante bienveillante du primaire en France. Réponds UNIQUEMENT "
        'avec un JSON valide {"objet":"...","corps":"..."} — pas de markdown.'
    )
    infos = (
        f"Prénom : {prenom}"
        + (f", Niveau : {niveau}" if niveau else "")
        + (f", Besoins : {besoins}" if besoins else "")
    )
    user = f"Rédige un mail de type « {type_} » pour les parents. Infos élève : {infos}. Concis, chaleureux."
    try:
        import json as _json

        res = ai_local.generate(user=user, system=system, max_tokens=600, cache=False)
        txt = res["text"].strip()
        if txt.startswith("```"):
            txt = txt.split("```")[1]
            txt = txt[4:] if txt.startswith("json") else txt
            txt = txt.strip()
        data = _json.loads(txt)
        if isinstance(data, dict) and "objet" in data and "corps" in data:
            return data, prenom, nom
    except Exception:
        pass
    return _apply_fallback(type_, prenom), prenom, nom


def run_due(auto_send=None, max_actions=3):
    """Exécute les automatisations dues. Appelé par le timer systemd (on-demand) ou la route.

    - Garde thermique : si la machine est déjà chaude, on reporte (pas d'inférence).
    - Prépare les mails dus (absence, bilan besoins, rappel sortie) et les journalise.
    - auto_send : n'envoie réellement que si activé (kv 'automation_auto_send'=1) ET SMTP configuré.
    Renvoie un dict résumé (jamais d'exception remontée au timer).
    """
    out = {
        "ok": True,
        "temp": _cpu_temp(),
        "prepares": 0,
        "envoyes": 0,
        "reporte": False,
        "details": [],
    }
    if out["temp"] >= _TEMP_MAX:
        out["reporte"] = True
        out["ok"] = False
        out["raison"] = (
            f"Surchauffe ({out['temp']}°C ≥ {_TEMP_MAX}°C) — automatisations reportées"
        )
        try:
            conn = _get_conn()
            _init_table(conn)
            _log(conn, "systeme", "scheduler", out["raison"])
            conn.close()
        except Exception:
            pass
        return out

    try:
        conn = _get_conn()
        _init_table(conn)
        if auto_send is None:
            auto_send = _kv_get(conn, "automation_auto_send", "0") == "1"
        suggestions = _collect_suggestions()
    except Exception as e:
        out["ok"] = False
        out["raison"] = f"Erreur collecte : {e}"
        return out

    # config SMTP partagée avec le module mailer (envoi réel optionnel)
    smtp_cfg = {}
    try:
        import mailer

        smtp_cfg = mailer._get_cfg()
    except Exception:
        mailer = None

    done = 0
    for s in suggestions:
        if done >= max_actions or _cpu_temp() >= _TEMP_MAX:
            break
        t = s.get("type")
        if t not in _MAIL_TYPES:
            continue
        type_mail = _MAIL_TYPES[t]
        eleve_id = s.get("eleve_id")
        mail, prenom, nom = _build_mail(conn, type_mail, eleve_id)
        cible = f"{prenom} {nom}".strip() or s.get("cible", "")
        sent = False
        # envoi réel seulement si demandé + config OK + email parent connu
        dest = ""
        if eleve_id:
            r = conn.execute(
                "SELECT email_parent FROM eleves WHERE id=?", (eleve_id,)
            ).fetchone()
            dest = (
                (r["email_parent"] or "").strip()
                if r and "email_parent" in r.keys()
                else ""
            )
        if auto_send and mailer and smtp_cfg and mailer._cfg_ready(smtp_cfg) and dest:
            try:
                mailer._send_smtp(smtp_cfg, dest, mail["objet"], mail["corps"])
                sent = True
                out["envoyes"] += 1
                conn.execute(
                    "INSERT INTO mail_log(dest,sujet,corps,eleve_id,statut) VALUES(?,?,?,?,?)",
                    (dest, mail["objet"], mail["corps"], eleve_id, "envoye"),
                )
                conn.commit()
            except Exception as e:
                _log(conn, "echec_envoi", cible, str(e)[:300])
        if not sent:
            import json as _json

            _log(
                conn,
                type_mail,
                cible,
                _json.dumps({**mail, "auto": True}, ensure_ascii=False),
            )
            out["prepares"] += 1
        out["details"].append({"type": type_mail, "cible": cible, "envoye": sent})
        done += 1

    conn.close()
    return out


def _route_run():
    from flask import request as _rq

    d = _rq.get_json(force=True, silent=True) or {}
    res = run_due(
        auto_send=d.get("auto_send"), max_actions=int(d.get("max_actions", 3))
    )
    return jsonify(res)


def _route_autosend():
    """GET: lit l'état. POST {on:bool}: active/désactive l'envoi automatique réel."""
    from flask import request as _rq

    conn = _get_conn()
    _init_table(conn)
    if _rq.method == "POST":
        on = "1" if (_rq.get_json(force=True, silent=True) or {}).get("on") else "0"
        conn.execute(
            "INSERT INTO kv(k,v) VALUES('automation_auto_send',?) "
            "ON CONFLICT(k) DO UPDATE SET v=excluded.v",
            (on,),
        )
        conn.commit()
    state = _kv_get(conn, "automation_auto_send", "0") == "1"
    conn.close()
    return jsonify({"auto_send": state})


# ---------------------------------------------------------------------------
# Enregistrement Flask
# ---------------------------------------------------------------------------


def register(app):
    app.add_url_rule(
        "/api/automations/run", "automations_run", _route_run, methods=["POST"]
    )
    app.add_url_rule(
        "/api/automations/auto-send",
        "automations_autosend",
        _route_autosend,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/api/automations/suggestions",
        "automations_suggestions",
        _route_suggestions,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/automations/mail-dynamique",
        "automations_mail_dynamique",
        _route_mail_dynamique,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/automations/planning-auto",
        "automations_planning_auto",
        _route_planning_auto,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/automations/log",
        "automations_log",
        _route_log,
        methods=["GET"],
    )
    print("[Pousseline] Automatisations chargé")


if __name__ == "__main__":
    # Appelé par le timer systemd (on-demand). Aucune boucle : exécute une fois et sort.
    import json as _json
    import sys as _sys

    if len(_sys.argv) > 1 and _sys.argv[1] == "run":
        print(_json.dumps(run_due(), ensure_ascii=False))
    else:
        print("usage: python3 automations.py run")
