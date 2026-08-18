#!/usr/bin/env python3
"""
manus_cli.py — Interface Ligne de Commande & Automatisation pour Manus AI v2
Permet de :
  - Lancer des tâches de recherche et moissonnage profond (Deep Research)
  - Interroger les crédits et l'état de l'API
  - Gérer les Agents Manus, sous-tâches, et thread IM principal
  - Exécuter les compétences financières, web scraping et analyse vidéo
  - Sauvegarder les résultats directement dans ~/labo/bibliotheque/

Auth : x-manus-api-key (clé dans ~/.config/jarvis/manus.env)
Base : https://api.manus.ai/v2
Shortcut IM : task_id='agent-default-main_task', agent_id='agent-default'
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, "/home/pamerys/jarvis/mcp")
from manus_mcp import call, API_KEY, ENV_FILE

OUTPUT_DIR = Path.home() / "labo" / "bibliotheque" / "docs" / "manus_harvest"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _check_auth() -> bool:
    """Vérifie que la clé API est présente. Affiche un guide sinon."""
    if API_KEY:
        return True
    print(f"❌ MANUS_API_KEY absente. Configurez-la dans : {ENV_FILE}")
    print("   → Générez une clé sur https://manus.im/app?show_settings=integrations&app_name=api")
    print("   → Ajoutez : MANUS_API_KEY=sk-... dans ~/.config/jarvis/manus.env")
    return False


def _print_error(res: dict, context: str = "") -> None:
    err = res.get("error") or {}
    code = err.get("code", "") if isinstance(err, dict) else str(err)
    msg  = err.get("message", str(err)) if isinstance(err, dict) else str(err)
    rid  = res.get("request_id", "")
    print(f"❌ {context}: [{code}] {msg}" + (f" (req_id={rid})" if rid else ""))


def cmd_credits() -> None:
    if not _check_auth(): return
    res = call("usage.availableCredits")
    if res.get("ok"):
        total   = res.get("total_credits", 0)
        free    = res.get("free_credits", 0)
        daily   = res.get("refresh_credits", 0)
        refresh = res.get("next_refresh_at", "—")
        print(f"💎 Crédits Manus : {total} total  (permanents: {free}, quotidien: {daily})")
        print(f"   Prochain rechargement : {refresh}")
    else:
        _print_error(res, "credits")


def cmd_skills() -> None:
    if not _check_auth(): return
    res = call("skill.list")
    if res.get("ok"):
        skills = res.get("data", [])
        print(f"✨ Compétences Manus disponibles ({len(skills)}) :")
        for s in skills:
            print(f"  • {s['name']:<30} : {s.get('description','')[:85]}...")
    else:
        _print_error(res, "skill.list")


def cmd_agents() -> None:
    """Liste les agents personnalisés + rappel du raccourci IM par défaut."""
    if not _check_auth(): return
    res = call("agent.list")
    if res.get("ok"):
        agents = res.get("data", [])
        print(f"🤖 Agents Manus ({len(agents)}) :")
        print(f"  • [SYSTÈME] agent-default  → Agent IM par défaut (raccourci universel)")
        for a in agents:
            print(f"  • {a.get('id','?')}  surnom={a.get('nickname','—')}  {a.get('description','')[:60]}")
        if not agents:
            print("  (Aucun agent personnalisé — seul l'agent IM est disponible)")
    else:
        _print_error(res, "agent.list")


def cmd_agent_detail(agent_id: str) -> None:
    if not _check_auth(): return
    res = call("agent.detail", {"agent_id": agent_id})
    if res.get("ok"):
        d = res.get("data") or res
        print(f"🤖 Agent [{agent_id}]")
        print(f"   Surnom      : {d.get('nickname')}")
        print(f"   Description : {d.get('description')}")
        print(f"   Main Task   : {d.get('task_id') or d.get('main_task_id')}")
    else:
        _print_error(res, f"agent.detail({agent_id})")


def cmd_subtasks(agent_id: str = "agent-default") -> None:
    """Liste les sous-tâches d'un agent (scope=agent_subtask)."""
    if not _check_auth(): return
    res = call("task.list", {"scope": "agent_subtask", "agent_id": agent_id, "limit": 20})
    if res.get("ok"):
        tasks = res.get("data", [])
        print(f"📋 Sous-tâches [{agent_id}] ({len(tasks)}) :")
        for t in tasks:
            print(f"  • {t.get('id')}  status={t.get('status')}  {(t.get('title') or t.get('name','Sans titre'))[:60]}")
    else:
        _print_error(res, f"subtasks({agent_id})")


def cmd_chat_im(message: str) -> None:
    """Envoie un message direct à l'Agent IM via le raccourci agent-default-main_task."""
    if not _check_auth(): return
    print(f"💬 [IM] → agent-default-main_task : {message[:80]}...")
    res = call("task.sendMessage", {
        "task_id": "agent-default-main_task",
        "message": {"content": message},
    })
    if res.get("ok"):
        print("  ✓ Message envoyé. Attente de la réponse...")
        time.sleep(4)
        msgs = call("task.listMessages", {
            "task_id": "agent-default-main_task",
            "order": "desc",
            "limit": 5,
        })
        if msgs.get("ok"):
            for m in reversed(msgs.get("data", [])):
                role    = m.get("role", "agent")
                content = m.get("content") or m.get("text") or ""
                if content:
                    icon = "🧑" if role == "user" else "🤖"
                    print(f"  {icon} [{role.upper()}] {content[:300]}")
        else:
            _print_error(msgs, "listMessages IM")
    else:
        err = res.get("error") or {}
        code = err.get("code", "") if isinstance(err, dict) else ""
        if code == "not_found":
            print("  ⚠️  Agent IM non trouvé — bascule sur task.create...")
            cmd_task(message)
        else:
            _print_error(res, "chat IM")


def cmd_task(prompt: str) -> None:
    if not _check_auth(): return
    print(f"🚀 [MANUS] Tâche autonome : {prompt[:80]}")
    res = call("task.create", {"message": {"content": prompt}, "agent_profile": "manus-1.6"})
    if res.get("ok"):
        task_id = res.get("task_id") or res.get("id")
        print(f"  ✓ ID tâche : {task_id}")
        print(f"  ⏳ Polling statut...")
        for _ in range(30):
            time.sleep(5)
            st_res = call("task.detail", {"task_id": task_id})
            st = st_res.get("status") or "running"
            print(f"     → {st}")
            if st in ["completed", "success", "failed", "stopped"]:
                break
    else:
        _print_error(res, "task.create")


def cmd_auth_check() -> None:
    """Diagnostic complet de l'authentification Manus API."""
    print("🔐 Diagnostic authentification Manus API v2")
    key = API_KEY
    if key:
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        print(f"   Clé API     : {masked}")
        print(f"   Source      : {ENV_FILE}")
        print(f"   Méthode     : x-manus-api-key (API Key)")
        # test live
        res = call("usage.availableCredits")
        if res.get("ok"):
            print(f"   Status live : ✅ Authentifié")
            print(f"   Crédits     : {res.get('total_credits', 0)}")
        else:
            err = res.get("error") or {}
            code = err.get("code","") if isinstance(err, dict) else str(err)
            print(f"   Status live : ❌ Erreur [{code}]")
    else:
        print(f"   ❌ MANUS_API_KEY non configurée dans {ENV_FILE}")
        print(f"   → Générer une clé : https://manus.im/app?show_settings=integrations&app_name=api")
        print(f"   → 50 clés max par compte. Rate limits partagées entre toutes les clés.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  manus auth                     - Diagnostic authentification API")
        print("  manus credits                  - Crédits disponibles")
        print("  manus skills                   - Compétences disponibles")
        print("  manus agents                   - Lister les agents")
        print("  manus agent <id>               - Détails d'un agent")
        print("  manus subtasks [agent_id]      - Sous-tâches d'un agent (défaut: agent-default)")
        print("  manus chat <message>           - Parler à l'Agent IM (agent-default-main_task)")
        print("  manus task <prompt>            - Lancer une tâche autonome standard")
        sys.exit(0)

    action = sys.argv[1]
    rest   = sys.argv[2:]

    if action == "auth":
        cmd_auth_check()
    elif action == "credits":
        cmd_credits()
    elif action == "skills":
        cmd_skills()
    elif action == "agents":
        cmd_agents()
    elif action == "agent":
        cmd_agent_detail(rest[0] if rest else "agent-default")
    elif action == "subtasks":
        cmd_subtasks(rest[0] if rest else "agent-default")
    elif action == "chat":
        msg = " ".join(rest)
        if not msg:
            print("❌ Fournir un message. Ex: manus chat Bonjour !")
            sys.exit(1)
        cmd_chat_im(msg)
    elif action == "task":
        prompt = " ".join(rest)
        if not prompt:
            print("❌ Fournir un prompt. Ex: manus task Analyse le marché IA 2025")
            sys.exit(1)
        cmd_task(prompt)
    else:
        cmd_task(" ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()
