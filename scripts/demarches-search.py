#!/usr/bin/env python3
import sys, json
from pathlib import Path

INDEX = Path.home() / 'jarvis/multiagent/demarches_index.json'
DEMARCHES = Path.home() / 'Documents/Windows-Import/demarches'

def main():
    args = sys.argv[1:]
    if not args or args[0] == '--all':
        idx = json.loads(INDEX.read_text())
        for d in idx:
            print(f"  {d['fichier']:40s} {d['titre'][:50]}")
        print(f"\nTotal: {len(idx)} démarches")
        return
    if args[0] == '--show' and len(args) > 1:
        query = args[1].lower()
        for f in DEMARCHES.glob('*.md'):
            if query in f.name.lower():
                print(f.read_text(encoding='utf-8', errors='ignore'))
                return
        print(f"Aucun fichier correspondant à '{query}'")
        return
    query = ' '.join(args).lower()
    idx = json.loads(INDEX.read_text())
    results = [d for d in idx if query in d['titre'].lower() or query in d['resume'].lower() or query in d['fichier'].lower()]
    if not results:
        print(f"Aucun résultat pour '{query}'")
        return
    for d in results:
        print(f"  📄 {d['fichier']}")
        print(f"     {d['titre']}")
        print(f"     {d['resume'][:100]}...")
        print()

if __name__ == '__main__':
    main()
