[user] Tu dépouilles des feuilles de route d'ambulance MANUSCRITES scannées (contentieux prud'homal, zéro invention tolérée).

IMAGES À LIRE (déjà tournées et contrastées, prêtes à lire) :
/tmp/fdrrot/avril-01.png à /tmp/fdrrot/avril-14.png (14 pages)

MÉTHODE OBLIGATOIRE : lis CHAQUE image, une par une, avec l'outil Read (vision). NE SAUTE AUCUNE PAGE. Ne devine jamais le contenu d'une page que tu n'as pas ouverte.

STRUCTURE DU FORMULAIRE (une feuille = une nuit) :
- En-tête : "Date: JJ/MM/26" | "Véhicule: <Rouge|Violette|R|V|...>" | "Chauffeur: <noms>" (ex. "SOUF / JOSH")
- Tableau, colonnes de gauche à droite :
  1) Équipage (ex. SOUF, JOSH, CHRIS, NICO...)
  2) Patient (nom de famille)
  3) Heure Départ
  4) Heure d'arrivée
  5) Lieu de Départ
  6) Lieu d'Arrivée  (souvent les deux lieux sont écrits d'un seul trait dans la case, ex. "URG LAP -> St Elois")
  7) BS+DT OK (ex. "BT+BS")
  8) Numéro SAMU (un numéro type "144.32" quand la mission vient du SAMU, vide sinon)

PIÈGE CONNU : l'écriture manuscrite DÉRIVE verticalement par rapport aux lignes imprimées. Une valeur peut apparaître décalée d'une demi-ligne. NE TE FIE PAS aux lignes du tableau : associe les valeurs par ORDRE (la k-ième valeur de chaque colonne = la k-ième mission). Vérifie que le nombre d'entrées est cohérent d'une colonne à l'autre ; si ce n'est pas cohérent, marque lisibilite=partiel.

CE QUE TU DOIS RENVOYER (texte brut, dans ton message final, PAS de fichier) :

=== SECTION 1 : CSV ===
Une ligne par MISSIO

[user] [Image: original 2090x656, displayed at 2000x628. Multiply coordinates by 1.04 to map to original image.]

[user] [Image: original 2800x400, displayed at 2000x286. Multiply coordinates by 1.40 to map to original image.]

[user] [Image: original 2800x416, displayed at 2000x297. Multiply coordinates by 1.40 to map to original image.]

[user] [Image: original 3798x280, displayed at 2000x147. Multiply coordinates by 1.90 to map to original image.]

[assistant] J'ai lu les 14 pages une par une (plus des recadrages/zooms sur les zones douteuses : colonne SAMU p.07, heures p.08/11/14, dates p.08/13, noms p.12/13).

=== SECTION 1 : CSV ===
```
2026-04-28;R;Souf;20h;20h30;Urg Lunel;Parc;non;avril-01;ok
2026-04-28;R;Souf;22h30;23h;Urg Lunel;Parc;non;avril-01;ok
2026-04-28;R;Josh;1h30;2h40;Urg beziers;Dom St Chinian;non;avril-01;ok
2026-04-28;R;Josh;2h50;3h30;Urg beziers;Dom bedarieux;non;avril-01;partiel
2026-04-27;R;Josh;20h;20h30;Urg Lunel;Parc;non;avril-02;partiel
2026-04-27;R;Josh;22h30;22h45;Urg st jean;Dom;non;avril-02;ok
2026-04-27;R;Josh;3h30;3h45;Urg mill;Dom mtp;non;avril-02;ok
2026-04-23;Rouge;JOSH;22h30;23h50;URG Millau;URG ADV;non;avril-03;partiel
2026-04-23;Rouge;SOUF;00h30;00h50;URG LAP;UTEC;non;avril-03;ok
2026-04-22;Rouge;JOSH;21h10;21h30;URG Mil;Dom Mtp;non;avril-04;ok
2026-04-22;Rouge;JOSH;00h10;01h00;URG Beziers;UTEC;non;avril-04;ok
2026-04-22;Rouge;SOUF;1h45;2h00;URG Beziers;Dom Beziers;non;avril-04;ok
2026-04-22;Rouge;SOUF;2h30;2h45;URG Beziers;Dom Beziers;non;avril-04;ok
2026-04-22;Rouge;SOUF;3h15;3h30;URG Beziers;Dom Beziers;non;avril-04;ok
2026-04-22;Rouge;SOUF;3h45;4h00;URG Beziers;Dom Beziers;non;avril-04;partiel
2026-04-19;Rouge;SOUF;20h00;20h30;URG St Roch;Millenaire;non;avril-05;ok
2026-04-19;Rouge;SOUF;21h30;22h00;URG St Jean;SSR LGM;non;avril-05;partiel
2026-04-19;Rouge;SOUF;00h30;00h50;URG LAP;Dom Mtp;non;avril-05;partiel
2026-04-19;Rouge;JOSH;1h55;2h35;URG LAP;Dom Lunel;non;avril-05;ok
2026-04-19;Rouge;S