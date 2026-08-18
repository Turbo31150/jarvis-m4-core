#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

WORKSPACES = Path("/home/pamerys/Workspaces")

def get_claude_content(repo_name, readme_content):
    prompt = f"""Génère un fichier CLAUDE.md concis en français pour le projet "{repo_name}" basé sur les informations de son README.md.
Le fichier CLAUDE.md doit contenir :
1. Les commandes de build et d'exécution les plus courantes.
2. Les commandes pour lancer les tests (spécifiques à la techno du projet si possible, ex: pytest, npm test, etc.).
3. Des instructions de style de code succinctes (ex: typage, gestion d'erreurs).

README.md :
{readme_content[:3000]}
"""
    try:
        # Appeler lm-ask.sh
        proc = subprocess.run(
            ["/bin/bash", "/home/pamerys/jarvis/scripts/lm-ask.sh", prompt],
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception as e:
        print(f"Erreur lors de la génération avec lm-ask: {e}")
    
    # Fallback générique
    return f"""# CLAUDE.md — Directives de développement pour {repo_name}

## Commandes de base
- Démarrage : command à définir
- Test : command à définir

## Style de Code
- Suivre les conventions standard du langage principal.
- Toujours commenter le code sensible.
"""

def main():
    print("Début de la création des CLAUDE.md...")
    for repo_path in WORKSPACES.iterdir():
        if not repo_path.is_dir() or repo_path.name.startswith("."):
            continue
        
        claude_md = repo_path / "CLAUDE.md"
        if claude_md.exists():
            print(f"CLAUDE.md existe déjà pour {repo_path.name}")
            continue
        
        readme_md = repo_path / "README.md"
        readme_content = ""
        if readme_md.exists():
            try:
                readme_content = readme_md.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                print(f"Erreur lecture README de {repo_path.name}: {e}")
        
        print(f"Génération de CLAUDE.md pour {repo_path.name}...")
        content = get_claude_content(repo_path.name, readme_content)
        try:
            claude_md.write_text(content, encoding="utf-8")
            print(f"✓ CLAUDE.md créé pour {repo_path.name}")
        except Exception as e:
            print(f"Erreur écriture CLAUDE.md pour {repo_path.name}: {e}")

if __name__ == "__main__":
    main()
