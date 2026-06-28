# Déploiement — sites-2026 (refonte)

> Sources corrigées des 9 sites, prêtes à mettre en ligne. **Le déploiement est ton action**
> (publier = ton compte Netlify). Branche git : `sites-2026-refonte`.

## 1. Déployer les 9 pages corrigées
Chaque fichier est une page autonome (HTML + CSS + JS inline, aucun asset externe).
Pour chaque site : Netlify → le projet → **Deploys** → glisser-déposer le `.html` correspondant
(ou `Deploys > Drag and drop`). Le nom du fichier = slug actuel du site.

| Fichier local | Site Netlify actuel |
|---|---|
| `alkymia-os.html` | alkymia-os |
| `alkymia-oss.html` | alkymia-oss |
| `admin-ia.html` | admin-ia |
| `agent-sans-coder.html` | agent-sans-coder |
| `transcription-ia-jarvis.html` | transcription-ia-jarvis |
| `reparation-ia.html` | reparation-ia |
| `euphonious-youtiao-56dd0d.html` | euphonious-youtiao-56dd0d |
| `bespoke-pony-491fd1.html` | bespoke-pony-491fd1 |
| `jarvis-products.html` | jarvis-products |

## 2. Renommer les slugs (Netlify → Site settings → Change site name)
| Actuel | → Nouveau | Marque |
|---|---|---|
| `euphonious-youtiao-56dd0d` | `automatia` | AutomatIA |
| `transcription-ia-jarvis` | `transcription-ia` | Franck Delmas |
| `bespoke-pony-491fd1` | `jarvis-academy` | JARVIS Academy |

⚠️ Après renommage, l'URL `.netlify.app` change : mettre à jour les liens/pubs qui pointaient
vers l'ancienne URL.

## 3. Déployer le correctif de sécurité PayPal (séparé)
Repo `jarvis-commercial-2026`, branche `fix-paypal-price-validation`. Concerne le site qui
héberge la fonction IPN (`jarvis-delmas`). Après déploiement :
- Test : faire un achat réel au **prix normal** → le PDF doit arriver.
- Vérifier dans les logs Netlify Functions qu'un montant falsifié donnerait `amount mismatch`.
- Vérifier aussi `jarvis-website/api/paypal-ipn.js` (handler Vercel dupliqué) : appliquer le même
  garde-fou s'il est déployé.

## 4. À compléter avant mise en ligne définitive
- **SIRET / statut juridique** dans les footers « Mentions légales » (marqué `TODO` en commentaire
  HTML sur les 5 sites B2C/AutomatIA).
- Vérifier que le compte PayPal marchand (`miningexpert31@gmail.com`) est bien le tien.

## 5. Récapitulatif des corrections déjà appliquées
- **Chiffres unifiés** : 1000+ agents · 12 GPU · <300ms (compteurs marketing globaux).
- **Bug réparé** : compteurs hero d'alkymia-oss qui affichaient « 0 ».
- **Témoignages anonymisés** : aucun nom/ville client (RGPD + art. L121-2).
- **Emails** : contact unifié `franckdelmas00@gmail.com` ; **compte marchand PayPal préservé**.
- **Mentions légales/RGPD** ajoutées sur les 5 sites qui en manquaient (LCEN art. 6).
- **bespoke-pony** repositionné en **JARVIS Academy** (lève la duplication des méga-sites).
- **Faille paiement PayPal** corrigée (validation prix serveur, 7 tests TDD).

## 6. Prochaine étape suggérée (non faite — décision de marque requise)
Identités visuelles distinctes par marque (palettes/typo) : aujourd'hui les 4 marques partagent
le même thème sombre. Restructuration profonde des méga-sites et upgrade capture leads
(mailto → Netlify Forms) à valider ensuite.
