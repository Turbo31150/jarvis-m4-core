[assistant] Je démarre par lire les slugs référencés dans les sites et tester les URLs réelles.

[assistant] Je teste maintenant les slugs réels au curl. Je lance un test HEAD sur tous les slugs uniques référencés.

[assistant] La garde thermique bloque (CPU 95°C). J'attends que ça refroidisse avant de relancer.

[assistant] La garde bloque tout Bash tant que le CPU est chaud. Je retente — la température fluctue vite.

[assistant] 7 slugs sur 66 sont morts. Je localise maintenant où les boutons cassés pointent dans les deux fichiers HTML, avec leur contexte (titre/prix).

[assistant] J'ai tout ce qu'il faut. Le magasin est vivant (root 200), 59 des 66 boutons encaissent déjà, seuls 7 slugs sont morts. Je transmets le plan au team-lead.

[assistant] Plan transmis au team-lead. Synthèse de ce que j'ai trouvé (rien modifié, uniquement du curl en lecture) :

**La boutique n'est pas cassée — elle a 7 trous.** Le store root `franckdelmas.gumroad.com/` répond 200, et sur les **66 slugs Gumroad** référencés dans les boutons « acheter » des deux sites (`~/jarvis/sites-2026/alkymia-os.html` et `bespoke-pony-491fd1.html`), **59 répondent déjà 200** et encaissent. Seuls **7 slugs sont morts (404)** :

| Slug 404 | Prix | Équivalent 200 existant ? |
|---|---|---|
| `pack-complet-jarvis-os` | **399 €** | ❌ produit phare |
| `jarvis-os-cluster-complet` | 149 € | ❌ |
| `agents-autonomes-mcp` | 99 € | ❌ |
| `ia-healthcare` | 79 € | ✅ `ia-sante` (doublon EN/FR) |
| `llms-locaux-lm-studio-ollama` | 79 € | ❌ |
| `jarvis-voice-ptt` | 69 € | ~ `jarvis-whisper-flow` (voisin) |
| `gemini-cli-masterclass` | 59 € | ❌ |

**Voie la plus rapide = hybride.** Repointer les liens (voie B) ne marche que pour `ia-healthcare→ia-sante` : les 5 autres, dont les 2 packs phares (399 € et 149 €), n'ont aucun équivalent existant, donc seul Franck peut les **republier** côté dashboard (un 404 Gumroad = produit en brouillon ou permalink ≠ slug attendu — c'est « republier / corriger l'URL », pas « recréer »).

**Recommandation chiffrée :** Franck republie en premier `pack-complet-jarvis-os` (399 €) + `jarvis-os-cluster-complet` (149 €) — ~5 min de dashboard qui débloquent 548 € de panier phare. En parallèle, moi je peux corriger `ia-healthcare→ia-sante` et poser 