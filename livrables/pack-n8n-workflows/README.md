# pack-n8n-workflows

Pack de workflows n8n prêts à importer, **scrubbés de tout credential**. Les
identifiants et jetons sont référencés par variable d'environnement n8n
(`{{ $env.* }}`), jamais en clair.

## Contenu
```
workflows/
  planning-prod-trigger.json            # déclencheur planning (webhook + auth par env)
  workflow_01_mail_surveillance.json    # surveillance boîte mail
  workflow_02_linkedin_automation.json  # automatisation LinkedIn
  workflow_03_network_expansion.json    # expansion réseau
  workflow_04_notebooklm_cloud_prospecting.json  # prospection via NotebookLM
README.md / FICHE-VENTE.md / LICENSE.txt
```

## Installation
1. Dans n8n : **Workflows → Import from File**, sélectionnez un `.json`.
2. Recréez vos **credentials** dans n8n (Settings → Credentials) et associez-les
   aux nodes concernés — aucun credential n'est fourni dans le pack.
3. Définissez les variables d'environnement référencées (ex.
   `PLANNING_TRIGGER_TOKEN`) côté n8n.
4. Activez le workflow.

## Sécurité
Aucun secret, jeton ni chemin personnel dans les fichiers : tout est paramétré.
Vérifiez / adaptez les chemins et credentials à votre environnement avant
activation.
