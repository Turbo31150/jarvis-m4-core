# TODO — profil `ecole`

Pousseline (PII élèves)

## À faire
- [ ] **Arbitrer les routeurs** : `cascade.py` (nouveau, sonde avant de router) coexiste avec
      `ai_local.py` (Gemini, ZAI, Ollama cloud, mais 2 backends morts sur 3). Soit corriger
      les adresses d'`ai_local.py` et lui greffer la sonde, soit le faire déléguer à `cascade.py`.
      Ne pas laisser deux routeurs diverger.
- [ ] **Auditer les modules non encore relus** pour le mode nominatif : `equipe.py`,
      `banque_annuelle.py`, `sorties.py`, `histoire.py`, `outils_classe.py`, `commandes.py`,
      `automations.py`, `edt.py`, `admin.py`, `assistant.py`, `scripts/dispatch_banque.py`.
      Règle : si le prompt contient un prénom, une appréciation ou une observation
      → `nominatif=True`. Sinon laisser sortir (qualité + cache).
- [ ] **Onglet front pour la cascade** : le backend est branché (`/api/cascade`), mais aucune
      section de `index.html` ne l'utilise — module orphelin tant que le front n'appelle pas.
- [ ] **Rendre le tunnel M6 persistant** : `127.0.0.1:11435` vient d'un `ssh -fN` manuel,
      il ne survivra pas à un redémarrage.

## Bloqué
- [ ] **SSH vers Rémi** — `tailnet policy does not permit you to SSH as user "turbo"`.
      Ce n'est pas un mot de passe : il manque une section `ssh` dans les ACL Tailscale
      (login.tailscale.com/admin/acls, `dst: autogroup:self`). Action humaine requise.
- [ ] **M1 hors ligne** dans Tailscale — seul son disque USB est lisible.

## Fait
- [x] Profil créé le 14/08/2026 — `profil ecole` pour y basculer
- [x] 14/08/2026 — `cascade.py` : routeur 0-token qui sonde avant de router (cache → déporté → local),
      garde thermique 82 °C, garde-fou RGPD `nominatif=True`. Branché dans `server.py`, testé de
      bout en bout (voir `REPORT.md`).
- [x] 14/08/2026 — corrigé le cache muet : la table `ai_cache` est en anglais
      (`key`/`answer`/`ts`), ~745 entrées déjà réutilisables gratuitement.
- [x] 14/08/2026 — **corrigé 3 appels IA cassés** dans `equipe.py` (ordre du jour de réunion,
      ×2) et `sorties.py` (mot aux parents). Deux bugs cumulés : arguments inversés
      (`generate(system, user)` alors que la signature est `generate(user, system=…)`, donc
      rôles à l'envers pour le modèle) **et** retour traité comme une chaîne alors que
      `generate()` renvoie un dict — le front recevait l'objet entier au lieu du texte.
      Ces fonctions ne pouvaient pas marcher correctement.
- [x] 14/08/2026 — **colmaté la sortie de données élèves hors du foyer.** Constat :
      733/745 entrées de cache venaient de `ollama-cloud` (ollama.com), et
      `ai_local.generate()` n'avait aucun garde-fou — prénoms, points forts, besoins et
      observations partaient à l'extérieur. Le `cache=False` déjà présent empêchait de
      *stocker*, pas d'*envoyer*. Fix : paramètre `nominatif=True` qui saute Z.AI, Gemini
      et Ollama Cloud et force `cache=False`. Activé sur les 6 appels nominatifs de
      `prof_routes.py` et `adaptatif.py`. Les 3 appels génériques (séance, cahier-journal,
      progression) continuent volontairement d'aller au cloud.
