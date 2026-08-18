[assistant] Confirmé — les quatre correctifs sont réels. Je lance `driver.sh smoke` pour obtenir les vrais chiffres avant de rédiger.

[assistant] Je mets à jour le fichier avec les quatre correctifs et les vrais chiffres relevés par `smoke`.

[assistant] Maintenant les Gotchas — j'insère les 4 correctifs à leur place logique, dans le même style que les entrées existantes.

[assistant] Frontmatter intact (`name: run-skillsmp`, description inchangée). Fichier passé de 145 à 184 lignes — j'ai resserré les entrées neuves au même format que l'existant plutôt que les empiler en bloc séparé.

[assistant] Terminé. Le rapport a été envoyé à `team-lead` — statut **DONE**.

Résumé : `/home/turbo/labo/bibliotheque/skillsmp/.claude/skills/run-skillsmp/SKILL.md` mis à jour avec les 4 correctifs (troncature GitHub→tarball, rapatriement récursif des annexes, écriture atomique du manifeste, détection des étages par nom de script) intégrés dans Gotchas/Troubleshooting/tableau des étages, et les chiffres de `smoke` rafraîchis avec la vraie sortie exécutée (`DRIVER OK (10/10)`, `conformes : 75/75`, `catalogue : 3069 skills · 525 avec code source · 324 mots-clés FR`). Frontmatter intact, `driver.sh` non modifié.