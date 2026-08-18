# site-aspirator — extraction code source + navigation (CDP, 0-token)

Avale le **code source réel** d'un site/app page par page via Chrome DevTools Protocol,
mémorise tout en local (HTML, DOM, CSS/JS détectés, navigation, chronologie des actions),
**adapte sa stratégie** à la structure (statique / SPA / dynamique-shadow-DOM) et produit
un rapport avec arbre de navigation Mermaid.

## Architecture (modulaire, couplage faible)

```
site-aspirator/
├── aspirator.py            # orchestrateur CLI + série d'actions (file BFS)
└── siteaspirator/
    ├── cdp.py              # canal CDP (WebSocket) — SEUL à parler au navigateur
    ├── protocol.py         # détection type de page → stratégie adaptative
    ├── capture.py          # extraction DOM/HTML/CSS/JS/navigation/balises/events
    ├── memory.py           # mémorisation locale (index/navigation/historique/logs)
    └── report.py           # rapport json + markdown + Mermaid
```

Chaque module a une responsabilité unique ; seul `cdp.py` touche Chrome (adaptateur),
le reste travaille sur des données pures → un module se remplace sans toucher les autres.

## Cycle (protocole)

```
navigate → detect(type) → adapte stratégie → capture(DOM,HTML,nav,ressources,events)
        → mémorise (HTML+capture.json+shot) → journalise → enfile liens internes → rapport
```

## Prérequis

Un Chrome pilotable en CDP (même canal que `cdp-inspect` / `notebooklm-aspire`) :
```bash
google-chrome --user-data-dir=/tmp/aspire --remote-debugging-port=9223 \
              --remote-allow-origins='*' https://exemple.org
```

## Usage

```bash
cd ~/jarvis/tools/site-aspirator
python3 aspirator.py aspire https://exemple.org --depth 1 --max-pages 10 --shots
python3 aspirator.py aspire                 # avale l'onglet CDP courant
python3 aspirator.py report ~/jarvis/data/aspirations/session-xxx

# via la bibliothèque-routeur :
bash ~/labo/bibliotheque/lib.sh run site-aspirator aspire https://exemple.org
```

## Sortie (mémoire locale)

```
~/jarvis/data/aspirations/session-<slug>/
├── pages/<slug>/index.html      # code source HTML avalé
├── pages/<slug>/capture.json    # nav + ressources + dom + events
├── pages/<slug>/shot.png        # capture d'état (option --shots)
├── index.json  navigation.json  historique.json  logs.jsonl
└── rapport.json  rapport.md      # rapport + arbre Mermaid
```

## Adaptation automatique (protocol.py)

| Type détecté | Signaux | Stratégie |
|---|---|---|
| **statique** | peu de scripts, `<a href>` nombreux | attente courte, pas de shadow, suit les hrefs |
| **spa** | framework (React/Angular/Vue…) + root app | attente + settle, traverse shadow-DOM, routes JS |
| **dynamique** | > 3 shadow hosts ou > 15 scripts | attente longue, shadow-DOM, hrefs |

## Notes

- 0-token : tout est capture + JS local, aucune inférence LLM.
- Chrome 136+ ignore `--remote-debugging-port` sur le profil défaut → `--user-data-dir` dédié.
- Réutilise le canal CDP validé de `bin/cdp-inspect.py` — voir
  `data/chrome-devtools-inspection-complete.md` pour le mapping domaines DevTools.
- N'aspire que ce qui est accessible dans l'onglet ; respecter les CGU/robots des sites tiers.
```
