# skills-library — bibliothèque vivante SkillsMP (JARVIS OS)

Moisson **bornée** de skillsmp.com → fiches locales normalisées, dédupliquées,
auditées. Aucun skill collecté n'est exécuté ; l'installation est une décision
séparée, après revue.

## Chaîne
```
skillsmp.com API (quota 50/j sans clé, 500/j avec SKILLSMP_API_KEY)
      │  ~/jarvis/bin/skillsmp-harvest.py run        (checkpoint atomique, backoff 429,
      │                                               arrêt à sec par mot-clé)
      ▼
raw/*.json  ──►  normalized/*.md  +  INDEX.jsonl  (dédup par id + SHA-256)
      │
      ├─ report  ──►  reports/harvest-*.md
      └─ export  ──►  skillsmp-export.json   (⚠ ne PAS passer à `skillsmp.py ingest` :
                                              il fait DELETE FROM skills → écraserait
                                              les ~199k skills de data/skillsmp.db)
```

## Commandes
```bash
python3 ~/jarvis/bin/skillsmp-harvest.py run [--max-requests N] [--keywords a,b] [--sort stars|recent]
python3 ~/jarvis/bin/skillsmp-harvest.py status    # checkpoint + quota du jour
python3 ~/jarvis/bin/skillsmp-harvest.py report    # rapport daté dans reports/
python3 ~/jarvis/bin/skillsmp-harvest.py export    # JSON consolidé (lecture seule)
```

## Mode permanent
- `scripts/resume_harvest.sh` — reprise depuis le checkpoint, fail-safe
- timer systemd user `skillsmp-harvest.timer` — quotidien 05:30 (+jitter 10 min),
  `Persistent=true` (rattrape si la machine dormait)

## Recherche locale (0 réseau)
- gros corpus FTS5 : `python3 ~/jarvis/bin/skillsmp.py search <mots>` (data/skillsmp.db, ~199k)
- fiches moissonnées : `grep -i <mot> INDEX.jsonl` ou `ls normalized/ | grep <mot>`

## Sécurité
Statuts possibles : `REVIEW_REQUIRED` (défaut — métadonnées seules, jamais « SAFE »
d'office), `DANGEROUS` (motif à risque détecté : rm -rf, curl|sh, reverse shell,
accès secrets, cryptomining…). Détail des motifs : en tête de
`~/jarvis/bin/skillsmp-harvest.py`.
