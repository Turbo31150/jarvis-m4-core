#!/usr/bin/env python3
"""Espace Prof — routes Flask (élèves, exercices différenciés, corrections,
séquences, cahier journal, mails parents). register(app) branché par server.py.
IA via ai_local (cascade adaptative 0-token). Données dans ecole.db (local/privé).

Sécurité RGPD : les routes /api/prof-* exigent un token (X-Prof-Token) car le
serveur écoute sur 0.0.0.0 (réseau local + PWA Android). Token auto-généré dans
~/jarvis/webapp/.prof_token ; la page /prof le demande une fois (localStorage).
"""

import hmac
import os
import secrets
import sqlite3
from datetime import date
from functools import wraps

from flask import jsonify, request, send_from_directory

import ai_local
from ecole_schema import ECOLE_DB, init_ecole_db

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOKEN_FILE = os.path.join(_HERE, ".prof_token")


def _load_token():
    try:
        return open(_TOKEN_FILE, encoding="utf-8").read().strip()
    except OSError:
        tok = secrets.token_urlsafe(24)
        try:
            with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(tok)
            os.chmod(_TOKEN_FILE, 0o600)
        except OSError:
            pass
        return tok


PROF_TOKEN = _load_token()


def require_token(fn):
    """Protège les données élèves. Localhost autorisé sans token (PC) ; réseau =
    token obligatoire (téléphone / autres appareils)."""

    @wraps(fn)
    def wrap(*a, **k):
        if request.remote_addr in ("127.0.0.1", "::1"):
            return fn(*a, **k)
        sent = request.headers.get("X-Prof-Token", "")
        if PROF_TOKEN and hmac.compare_digest(sent, PROF_TOKEN):  # constant-time
            return fn(*a, **k)
        return jsonify({"error": "non autorisé", "need_token": True}), 401

    return wrap


def _body():
    return request.get_json(force=True, silent=True) or {}


def _clamp(v, default, lo, hi):
    try:
        return max(lo, min(int(v), hi))
    except (TypeError, ValueError):
        return default


def _rows(q, args=()):
    c = sqlite3.connect(str(ECOLE_DB))
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(q, args).fetchall()]
    finally:
        c.close()


def _write(q, args=()):
    c = sqlite3.connect(str(ECOLE_DB))
    try:
        cur = c.execute(q, args)
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def register(app):
    init_ecole_db()

    @app.route("/prof")
    def prof_page():
        return send_from_directory(_HERE, "prof.html")

    @app.route("/api/prof/ia-status")
    @require_token
    def prof_ia_status():
        return jsonify(ai_local.backend_status())

    # ── ÉLÈVES ───────────────────────────────────────────────────────────
    @app.route("/api/eleves", methods=["GET"])
    @require_token
    def eleves_get():
        return jsonify(_rows("SELECT * FROM eleves ORDER BY niveau, nom LIMIT 500"))

    @app.route("/api/eleves", methods=["POST"])
    @require_token
    def eleves_add():
        d = _body()
        try:
            eid = _write(
                "INSERT INTO eleves(nom,prenom,niveau,groupe,points_forts,besoins,email_parent) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    d.get("nom", ""),
                    d.get("prenom", ""),
                    d.get("niveau", ""),
                    d.get("groupe", ""),
                    d.get("points_forts", ""),
                    d.get("besoins", ""),
                    str(d.get("email_parent", ""))[:200],
                ),
            )
            return jsonify({"id": eid, "ok": True})
        except Exception as e:
            return jsonify({"error": f"sauvegarde échouée: {e}"}), 500

    @app.route("/api/eleves/<int:eid>", methods=["PATCH", "DELETE"])
    @require_token
    def eleves_edit(eid):
        if request.method == "DELETE":
            _write("DELETE FROM eleves WHERE id=?", (eid,))
            return jsonify({"ok": True})
        d = _body()
        cols = [
            k
            for k in (
                "nom",
                "prenom",
                "niveau",
                "groupe",
                "points_forts",
                "besoins",
                "email_parent",
            )
            if k in d
        ]
        if not cols:
            return jsonify({"ok": True})
        sets = ", ".join(f"{c}=?" for c in cols)
        _write(f"UPDATE eleves SET {sets} WHERE id=?", (*[d[c] for c in cols], eid))
        return jsonify({"ok": True})

    # ── EXERCICES DIFFÉRENCIÉS ───────────────────────────────────────────
    @app.route("/api/exercice/generer", methods=["POST"])
    @require_token
    def exercice_generer():
        d = _body()
        matiere = str(d.get("matiere", "maths"))[:40]
        niveau = str(d.get("niveau", "CE2"))[:8]
        notion = str(d.get("notion", ""))[:120]
        nb = _clamp(d.get("nb", 5), 5, 1, 30)
        profil = ""
        # PII : si on personnalise pour un élève nommé, on NE met PAS en cache.
        use_cache = True
        if d.get("eleve_id"):
            e = _rows("SELECT * FROM eleves WHERE id=?", (d["eleve_id"],))
            if e:
                profil = (
                    f"\nAdapte au profil : points forts={e[0]['points_forts']}, "
                    f"besoins={e[0]['besoins']}."
                )
                use_cache = False
        prompt = (
            f"Crée {nb} exercices de {matiere} niveau {niveau} sur « {notion} » pour le "
            f"primaire.{profil}\nDonne TROIS versions séparées :\n"
            "## SOUTIEN (plus simple, étayé)\n## STANDARD\n## APPROFONDISSEMENT\n"
            "Inclus le corrigé de chaque version. Markdown, prêt à imprimer."
        )
        try:
            res = ai_local.generate(
                prompt,
                max_tokens=1100,
                cache=use_cache,
                nominatif=bool(d.get("eleve_id")),  # profil élève → reste dans le foyer
            )
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        try:
            xid = _write(
                "INSERT INTO exercices(titre,matiere,niveau,notion,contenu_md,eleve_id,backend) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    f"{matiere} — {notion} ({niveau})",
                    matiere,
                    niveau,
                    notion,
                    res["text"],
                    d.get("eleve_id"),
                    res["backend"],
                ),
            )
        except Exception:
            xid = None
        return jsonify(
            {
                "id": xid,
                "contenu_md": res["text"],
                "backend": res["backend"],
                "cached": res["cached"],
            }
        )

    @app.route("/api/exercices")
    @require_token
    def exercices_list():
        return jsonify(
            _rows(
                "SELECT id,titre,matiere,niveau,notion,created_at "
                "FROM exercices ORDER BY id DESC LIMIT 100"
            )
        )

    # ── CORRECTIONS ──────────────────────────────────────────────────────
    @app.route("/api/exercice/corriger", methods=["POST"])
    @require_token
    def exercice_corriger():
        d = _body()
        enonce = str(d.get("enonce", ""))[:1000]
        reponse = str(d.get("reponse_eleve", ""))[:2000]
        niveau = str(d.get("niveau", "CE2"))[:8]
        prompt = (
            f"Tu corriges la copie d'un élève de {niveau}. Énoncé : {enonce}\n"
            f"Réponse de l'élève : {reponse}\n\n"
            "Donne : 1) ce qui est juste, 2) erreurs expliquées simplement, "
            "3) conseil bienveillant, 4) note sur 10. Ton encourageant."
        )
        try:
            # copie d'un élève réel → ne sort pas du foyer
            res = ai_local.generate(
                prompt, max_tokens=900, cache=False, nominatif=True
            )
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        try:
            _write(
                "INSERT INTO corrections(exercice_id,eleve_id,enonce,reponse,feedback) "
                "VALUES(?,?,?,?,?)",
                (d.get("exercice_id"), d.get("eleve_id"), enonce, reponse, res["text"]),
            )
        except Exception:
            pass
        return jsonify({"feedback": res["text"], "backend": res["backend"]})

    # ── SÉQUENCES / CAHIER JOURNAL ───────────────────────────────────────
    @app.route("/api/sequence/generer", methods=["POST"])
    @require_token
    def sequence_generer():
        d = _body()
        sujet = str(d.get("sujet", ""))[:120]
        niveau = str(d.get("niveau", "CE2"))[:8]
        duree = _clamp(d.get("duree", 45), 45, 10, 180)
        prompt = (
            f"Prépare une séance de {duree} min, niveau {niveau}, sur « {sujet} ».\n"
            "Structure : Objectifs (compétences programme), Matériel, Déroulé minuté, "
            "Différenciation, Trace écrite. Markdown."
        )
        try:
            res = ai_local.generate(prompt, max_tokens=1500)
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        try:
            sid = _write(
                "INSERT INTO sequences(titre,sujet,niveau,duree_min,contenu_md) "
                "VALUES(?,?,?,?,?)",
                (sujet, sujet, niveau, duree, res["text"]),
            )
        except Exception:
            sid = None
        return jsonify(
            {"id": sid, "contenu_md": res["text"], "backend": res["backend"]}
        )

    @app.route("/api/cahier-journal", methods=["GET", "POST"])
    @require_token
    def cahier_journal():
        if request.method == "POST":
            d = _body()
            jour = d.get("date") or date.today().isoformat()
            try:
                _write(
                    "INSERT INTO cahier_journal(date,contenu_md) VALUES(?,?) "
                    "ON CONFLICT(date) DO UPDATE SET contenu_md=excluded.contenu_md",
                    (jour, str(d.get("contenu_md", ""))),
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            return jsonify({"ok": True, "date": jour})
        return jsonify(
            _rows("SELECT * FROM cahier_journal ORDER BY date DESC LIMIT 60")
        )

    # ── MAILS PARENTS ────────────────────────────────────────────────────
    @app.route("/api/mail-parent/draft", methods=["POST"])
    @require_token
    def mail_parent_draft():
        d = _body()
        motif = str(d.get("motif", ""))[:500]
        eleve = ""
        if d.get("eleve_id"):
            e = _rows("SELECT prenom,nom FROM eleves WHERE id=?", (d["eleve_id"],))
            if e:
                eleve = f"{e[0]['prenom']} {e[0]['nom']}"
        prompt = (
            f"Rédige un email court et bienveillant d'une enseignante aux parents "
            f"{'de ' + eleve if eleve else ''} au sujet : {motif}. "
            "Ton professionnel chaleureux, vouvoiement, prêt à envoyer. Objet + corps."
        )
        try:
            res = ai_local.generate(
                prompt,
                max_tokens=600,
                cache=not eleve,
                nominatif=bool(eleve),  # mail nommant un élève → reste dans le foyer
            )
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        return jsonify({"draft": res["text"], "backend": res["backend"]})

    # ── HISTORIQUE CORRECTIONS ───────────────────────────────────────────
    @app.route("/api/corrections", methods=["GET"])
    @require_token
    def corrections_list():
        eid = request.args.get("eleve_id")
        base = (
            "SELECT c.*, e.prenom, e.nom FROM corrections c "
            "LEFT JOIN eleves e ON e.id=c.eleve_id "
        )
        if eid:
            return jsonify(
                _rows(base + "WHERE c.eleve_id=? ORDER BY c.id DESC LIMIT 100", (eid,))
            )
        return jsonify(_rows(base + "ORDER BY c.id DESC LIMIT 100"))

    # ── APPEL / PRÉSENCES ────────────────────────────────────────────────
    @app.route("/api/presence", methods=["GET", "POST"])
    @require_token
    def presence():
        if request.method == "POST":
            d = _body()
            jour = d.get("date") or date.today().isoformat()
            saved = 0
            for it in d.get("presences") or []:
                try:
                    _write(
                        "INSERT INTO presence(eleve_id,date,present) VALUES(?,?,?) "
                        "ON CONFLICT(eleve_id,date) DO UPDATE SET present=excluded.present",
                        (it.get("eleve_id"), jour, 1 if it.get("present", True) else 0),
                    )
                    saved += 1
                except Exception:
                    pass
            return jsonify({"ok": True, "date": jour, "saved": saved})
        jour = request.args.get("date") or date.today().isoformat()
        return jsonify(
            _rows(
                "SELECT e.id AS eleve_id, e.prenom, e.nom, e.niveau, "
                "COALESCE(p.present,1) AS present "
                "FROM eleves e LEFT JOIN presence p "
                "ON p.eleve_id=e.id AND p.date=? ORDER BY e.niveau, e.nom",
                (jour,),
            )
        )

    # ── DIFFÉRENCIATION PAR ÉLÈVE (1 notion → N variantes adaptées) ──────
    @app.route("/api/exercice/differencier", methods=["POST"])
    @require_token
    def exercice_differencier():
        d = _body()
        matiere = str(d.get("matiere", "maths"))[:40]
        niveau = str(d.get("niveau", "CE2"))[:8]
        notion = str(d.get("notion", ""))[:120]
        nb = _clamp(d.get("nb", 3), 3, 1, 10)
        ids = d.get("eleve_ids") or []
        if not isinstance(ids, list) or not ids:
            return jsonify({"error": "Sélectionne au moins un élève"}), 400
        ids = ids[:6]  # plafond : IA locale lente, évite surcharge/thermique
        out = []
        for eid in ids:
            e = _rows("SELECT * FROM eleves WHERE id=?", (eid,))
            if not e:
                continue
            el = e[0]
            profil = (
                f"points forts={el['points_forts'] or '—'}, "
                f"besoins={el['besoins'] or '—'}"
            )
            prompt = (
                f"Crée {nb} exercices de {matiere} niveau {niveau} sur « {notion} » "
                f"pour {el['prenom']}, élève de primaire. Adapte précisément à son "
                f"profil ({profil}) : ajuste difficulté, étayage et consignes. "
                "Inclus le corrigé. Markdown, prêt à imprimer."
            )
            try:
                # prompt contenant le prénom et le profil de l'élève → ne sort pas du foyer
                res = ai_local.generate(
                    prompt, max_tokens=900, cache=False, nominatif=True
                )
            except ai_local.AIUnavailable as ex:
                return jsonify({"error": str(ex), "partiel": out}), 503
            try:
                _write(
                    "INSERT INTO exercices"
                    "(titre,matiere,niveau,notion,contenu_md,eleve_id,backend) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (
                        f"{matiere} — {notion} (adapté {el['prenom']})",
                        matiere,
                        niveau,
                        notion,
                        res["text"],
                        eid,
                        res["backend"],
                    ),
                )
            except Exception:
                pass
            out.append(
                {
                    "eleve_id": eid,
                    "prenom": el["prenom"],
                    "contenu_md": res["text"],
                    "backend": res["backend"],
                }
            )
        return jsonify({"variantes": out, "count": len(out)})

    # ── BULLETINS / LSU / SYNTHÈSES (PII → jamais en cache) ──────────────
    @app.route("/api/prof/bulletin", methods=["POST"])
    @require_token
    def prof_bulletin():
        d = _body()
        eid = d.get("eleve_id")
        e = _rows("SELECT * FROM eleves WHERE id=?", (eid,)) if eid else []
        if not e:
            return jsonify({"error": "élève introuvable"}), 400
        el = e[0]
        periode = str(d.get("periode", "Période 1"))[:30]
        typ = d.get("type", "appreciation")
        obs = str(d.get("observations", ""))[:1500]
        # notes de l'élève (suivi) pour contextualiser
        notes = el.get("notes_json", "{}")
        if typ == "lsu":
            consigne = (
                "Rédige une SYNTHÈSE pour le Livret Scolaire Unique (LSU) : "
                "bilan par domaines d'apprentissage, objectifs atteints, "
                "axes de progrès. Style officiel mais bienveillant."
            )
        elif typ == "synthese":
            consigne = (
                "Rédige une synthèse de suivi de l'élève pour l'équipe éducative : "
                "points forts, difficultés, aménagements utiles."
            )
        else:
            consigne = (
                "Rédige une APPRÉCIATION de bulletin (3-5 phrases) : "
                "constat bienveillant, progrès, conseil concret. "
                "Évite les formules vides, sois personnalisé et positif."
            )
        prompt = (
            f"{consigne}\nÉlève : {el['prenom']} ({el.get('niveau', '')}), {periode}.\n"
            f"Points forts : {el.get('points_forts', '')}. Besoins : {el.get('besoins', '')}.\n"
            f"Observations de l'enseignante : {obs}\nNotes : {notes}"
        )
        try:
            # PII : prénom, points forts, besoins, observations → ne sort pas du foyer
            res = ai_local.generate(
                prompt, max_tokens=700, cache=False, nominatif=True
            )
        except ai_local.AIUnavailable as ex:
            return jsonify({"error": str(ex)}), 503
        try:
            _write(
                "INSERT INTO bulletins(eleve_id,periode,type,contenu_md) VALUES(?,?,?,?)",
                (eid, periode, typ, res["text"]),
            )
        except Exception:
            pass
        return jsonify(
            {"contenu_md": res["text"], "backend": res["backend"], "type": typ}
        )

    @app.route("/api/prof/bulletins", methods=["GET"])
    @require_token
    def prof_bulletins_list():
        eid = request.args.get("eleve_id")
        if eid:
            return jsonify(
                _rows(
                    "SELECT * FROM bulletins WHERE eleve_id=? "
                    "ORDER BY id DESC LIMIT 50",
                    (eid,),
                )
            )
        return jsonify(
            _rows(
                "SELECT b.*, e.prenom, e.nom FROM bulletins b "
                "LEFT JOIN eleves e ON e.id=b.eleve_id "
                "ORDER BY b.id DESC LIMIT 100"
            )
        )

    # ── CAHIER-JOURNAL AUTO (depuis emploi du temps / séances du jour) ──
    @app.route("/api/cahier-journal/generer", methods=["POST"])
    @require_token
    def cahier_journal_generer():
        import json as _json

        d = _body()
        jour = d.get("date") or date.today().isoformat()
        niveau = str(d.get("niveau", ""))[:8]
        emploi = str(d.get("emploi_du_temps", ""))[:1500]
        # auto : si pas d'emploi fourni, lire l'EDT enregistré pour le jour de la semaine
        if not emploi.strip():
            try:
                from datetime import datetime as _dt

                jours = [
                    "lundi",
                    "mardi",
                    "mercredi",
                    "jeudi",
                    "vendredi",
                    "samedi",
                    "dimanche",
                ]
                wd = jours[_dt.fromisoformat(jour).weekday()]
                r = _rows("SELECT v FROM kv WHERE k='edt'")
                edt = _json.loads(r[0]["v"]) if r else {}
                emploi = str(edt.get(wd, ""))[:1500]
            except Exception:
                pass
        prompt = (
            f"Rédige le cahier-journal du {jour}"
            f"{' (classe ' + niveau + ')' if niveau else ''} pour une prof des écoles. "
            f"Emploi du temps / séances prévues :\n{emploi}\n\n"
            "Pour chaque créneau : objectif, activités, organisation, différenciation, "
            "observations à compléter. Concis, prêt à imprimer. Markdown."
        )
        try:
            res = ai_local.generate(prompt, max_tokens=1500)
        except ai_local.AIUnavailable as ex:
            return jsonify({"error": str(ex)}), 503
        try:
            _write(
                "INSERT INTO cahier_journal(date,contenu_md) VALUES(?,?) "
                "ON CONFLICT(date) DO UPDATE SET contenu_md=excluded.contenu_md",
                (jour, res["text"]),
            )
        except Exception:
            pass
        return jsonify(
            {"date": jour, "contenu_md": res["text"], "backend": res["backend"]}
        )

    # ── EXPORT vers ~/Documents/Classe (SQL → fichiers .md, rejouable) ──
    @app.route("/api/prof/export", methods=["POST"])
    @require_token
    def prof_export():
        base = os.path.expanduser("~/Documents/Classe")

        def slug(s, n=50):
            s = (
                "".join(
                    ch if (ch.isalnum() or ch in " -_") else "" for ch in str(s or "")
                )
                .strip()
                .replace(" ", "_")
            )
            return s[:n] or "sans_titre"

        def dump(sub, rows, title_fn, body_fn):
            d = os.path.join(base, sub)
            os.makedirs(d, exist_ok=True)
            cnt = 0
            for r in rows:
                fn = f"{(r.get('created_at') or r.get('date') or '')[:10]}_{r['id']:04d}_{slug(title_fn(r))}.md"
                try:
                    with open(os.path.join(d, fn), "w", encoding="utf-8") as f:
                        f.write(body_fn(r))
                    cnt += 1
                except OSError:
                    pass
            return cnt

        try:
            res = {
                "exercices": dump(
                    "exercices",
                    _rows("SELECT * FROM exercices ORDER BY id"),
                    lambda r: f"{r['matiere']}_{r['notion']}_{r['niveau']}",
                    lambda r: f"# {r['titre']}\n\n{r['contenu_md'] or ''}",
                ),
                "seances": dump(
                    "seances",
                    _rows("SELECT * FROM sequences ORDER BY id"),
                    lambda r: f"{r['sujet']}_{r['niveau']}",
                    lambda r: (
                        f"# Séance — {r['sujet']} ({r['niveau']})\n\n{r['contenu_md'] or ''}"
                    ),
                ),
                "bulletins": dump(
                    "bulletins",
                    _rows(
                        "SELECT b.*, e.prenom, e.nom FROM bulletins b "
                        "LEFT JOIN eleves e ON e.id=b.eleve_id ORDER BY b.id"
                    ),
                    lambda r: (
                        f"{r.get('prenom', '')}_{r.get('nom', '')}_{r['periode']}_{r['type']}"
                    ),
                    lambda r: (
                        f"# {r.get('prenom', '')} {r.get('nom', '')} — {r['periode']} ({r['type']})\n\n{r['contenu_md'] or ''}"
                    ),
                ),
                "cahier_journal": dump(
                    "cahier_journal",
                    _rows("SELECT * FROM cahier_journal ORDER BY date"),
                    lambda r: f"cahier_{r['date']}",
                    lambda r: (
                        f"# Cahier-journal {r['date']}\n\n{r['contenu_md'] or ''}"
                    ),
                ),
                "programmations": dump(
                    "programmations",
                    _rows("SELECT * FROM programmations ORDER BY id"),
                    lambda r: f"{r['matiere']}_{r['niveau']}_{r['portee']}",
                    lambda r: (
                        f"# Programmation {r['matiere']} {r['niveau']} ({r['portee']})\n\n{r['contenu_md'] or ''}"
                    ),
                ),
            }
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"ok": True, "dossier": base, "exportes": res})

    # ── PROGRAMMATIONS ANNUELLES / PROGRESSIONS ──────────────────────────
    @app.route("/api/prof/programmation", methods=["POST"])
    @require_token
    def prof_programmation():
        d = _body()
        matiere = str(d.get("matiere", "français"))[:40]
        niveau = str(d.get("niveau", "CE2"))[:8]
        portee = "periode" if d.get("portee") == "periode" else "annuelle"
        periode = str(d.get("periode", ""))[:30]
        if portee == "periode":
            consigne = (
                f"Établis la PROGRESSION de la {periode or 'période 1'} en {matiere} "
                f"pour le niveau {niveau} : séquences/notions dans l'ordre, "
                "compétences du B.O. visées, nombre de séances estimé."
            )
        else:
            consigne = (
                f"Établis la PROGRAMMATION ANNUELLE en {matiere} pour le niveau "
                f"{niveau} : répartition par période (P1 à P5), notions clés, "
                "compétences du B.O., progressivité sur l'année."
            )
        prompt = consigne + " Tableau/liste clair, prêt à l'emploi. Markdown."
        try:
            res = ai_local.generate(prompt, max_tokens=1600)
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        try:
            pid = _write(
                "INSERT INTO programmations(matiere,niveau,portee,periode,contenu_md) "
                "VALUES(?,?,?,?,?)",
                (matiere, niveau, portee, periode, res["text"]),
            )
        except Exception:
            pid = None
        return jsonify(
            {"id": pid, "contenu_md": res["text"], "backend": res["backend"]}
        )

    @app.route("/api/prof/programmations", methods=["GET"])
    @require_token
    def prof_programmations_list():
        return jsonify(
            _rows(
                "SELECT id,matiere,niveau,portee,periode,created_at "
                "FROM programmations ORDER BY id DESC LIMIT 100"
            )
        )

    # ── DASHBOARD ACCUEIL (synthèse) ─────────────────────────────────────
    @app.route("/api/prof/dashboard")
    @require_token
    def prof_dashboard():
        def n(t):
            try:
                return _rows(f"SELECT COUNT(*) AS c FROM {t}")[0]["c"]
            except Exception:
                return 0

        cj = _rows(
            "SELECT contenu_md FROM cahier_journal WHERE date=?",
            (date.today().isoformat(),),
        )
        return jsonify(
            {
                "eleves": n("eleves"),
                "exercices": n("exercices"),
                "sequences": n("sequences"),
                "bulletins": n("bulletins"),
                "programmations": n("programmations"),
                "corrections": n("corrections"),
                "cahier_aujourdhui": bool(cj and cj[0]["contenu_md"]),
                "ia": ai_local.backend_status(),
            }
        )

    # ── EMPLOI DU TEMPS (grille hebdo, alimente le cahier-journal auto) ──
    @app.route("/api/prof/edt", methods=["GET", "POST"])
    @require_token
    def prof_edt():
        import json as _json

        if request.method == "POST":
            d = _body()
            _write(
                "INSERT INTO kv(k,v) VALUES('edt',?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v,ts=datetime('now')",
                (_json.dumps(d.get("edt", {})),),
            )
            return jsonify({"ok": True})
        r = _rows("SELECT v FROM kv WHERE k='edt'")
        return jsonify(_json.loads(r[0]["v"]) if r else {})

    # ── ÉVALUATIONS / COMPÉTENCES / MOYENNES / GROUPES DE BESOIN ─────────
    @app.route("/api/prof/eval", methods=["GET", "POST"])
    @require_token
    def prof_eval():
        if request.method == "POST":
            d = _body()
            _write(
                "INSERT INTO evaluations(eleve_id,matiere,competence,note,sur,periode) "
                "VALUES(?,?,?,?,?,?)",
                (
                    d.get("eleve_id"),
                    str(d.get("matiere", ""))[:40],
                    str(d.get("competence", ""))[:80],
                    _clamp(d.get("note", 0), 0, 0, 100),
                    _clamp(d.get("sur", 10), 10, 1, 100),
                    str(d.get("periode", ""))[:30],
                ),
            )
            return jsonify({"ok": True})
        eid = request.args.get("eleve_id")
        if eid:
            return jsonify(
                _rows(
                    "SELECT * FROM evaluations WHERE eleve_id=? "
                    "ORDER BY id DESC LIMIT 200",
                    (eid,),
                )
            )
        return jsonify(_rows("SELECT * FROM evaluations ORDER BY id DESC LIMIT 200"))

    @app.route("/api/prof/eval/bilan")
    @require_token
    def prof_eval_bilan():
        # moyenne /20 par élève + groupe de besoin
        rows = _rows(
            "SELECT e.id, e.prenom, e.nom, e.niveau, "
            "AVG(v.note*20.0/v.sur) AS moy, COUNT(v.id) AS nb "
            "FROM eleves e LEFT JOIN evaluations v ON v.eleve_id=e.id "
            "GROUP BY e.id ORDER BY moy DESC"
        )
        out = []
        for r in rows:
            moy = round(r["moy"], 1) if r["moy"] is not None else None
            grp = "—"
            if moy is not None:
                grp = (
                    "soutien"
                    if moy < 10
                    else ("approfondissement" if moy >= 15 else "standard")
                )
            out.append(
                {
                    "eleve_id": r["id"],
                    "prenom": r["prenom"],
                    "nom": r["nom"],
                    "niveau": r["niveau"],
                    "moyenne": moy,
                    "nb": r["nb"],
                    "groupe": grp,
                }
            )
        return jsonify(out)

    # ── DICTÉE VOCALE (proxy vers Whisper :8789 + post-correction BDQT) ──
    @app.route("/api/prof/dictee", methods=["POST"])
    @require_token
    def prof_dictee():
        import urllib.request

        d = _body()
        audio = d.get("audio", "")
        fmt = str(d.get("format", "webm"))[:8]
        if not audio:
            return jsonify({"error": "pas d'audio"}), 400
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8789/",
                data=__import__("json")
                .dumps(
                    {
                        "audio": audio,
                        "format": fmt,
                        "language": "fr",
                        "context": "ecole",
                    }
                )
                .encode(),
                headers={"Content-Type": "application/json"},
            )
            r = __import__("json").loads(urllib.request.urlopen(req, timeout=60).read())
            return jsonify({"text": r.get("text", "")})
        except Exception as e:
            return jsonify({"error": f"transcription indisponible: {e}"}), 503

    return app
