[user] Tu fais une recherche bibliographique d'ingénierie fiabilité pour un rapport technique. Utilise WebSearch et WebFetch (charge-les via ToolSearch "select:WebSearch,WebFetch"). NE FABRIQUE AUCUN CHIFFRE. Chaque chiffre doit venir d'une source avec URL vérifiable que tu as réellement lue.

Sujet : usure d'un GPU silicium (TSMC 12nm, NVIDIA TU116) fonctionnant en permanence à 85-88 °C de température de jonction rapportée, contre 60-65 °C.

Cherche et rapporte, avec citation exacte + URL :

1. **Arrhenius / facteur d'accélération thermique**
   - La formule AF = exp[(Ea/k)(1/Tuse - 1/Tstress)], valeurs typiques d'Ea pour les mécanismes de défaillance semiconducteurs (électromigration ~0.7-0.9 eV, TDDB, NBTI, corrosion). Sources : JEDEC JEP122 (Failure Mechanisms and Models for Semiconductor Devices), JESD85, notes d'application de fabricants (TI, Microchip, ON Semi, Infineon), Sandia/NASA.
   - Calcule le facteur d'accélération 65 °C -> 87 °C pour plusieurs Ea, mais donne la formule et les Ea sourcés, pas des résultats inventés.

2. **Électromigration — loi de Black**
   MTTF = A·J^-n·exp(Ea/kT). Valeurs de n et Ea pour interconnexions cuivre. Sources académiques/JEDEC. Note bien : la loi de Black porte sur la température du MÉTAL d'interconnexion, pas la jonction lue par capteur.

3. **Condensateurs électrolytiques / polymère sur PCB GPU**
   - Règle « 10 °C = demi-vie » (Arrhenius) pour électrolytiques aluminium ; validité et limites pour condensateurs polymère solide (souvent 2

[assistant] I'll research this systematically, starting with the core reliability physics sources.

[assistant] The Arrhenius/EM foundation is solid. Now the capacitor and Coffin-Manson sections.

[assistant] ---

# RAPPORT BIBLIOGRAPHIQUE — Usure silicium GPU TU116 (TSMC 12 nm) à 85-88 °C vs 60-65 °C

**Règle appliquée** : chaque chiffre ci-dessous provient d'une source que j'ai réellement lue (PDF extrait localement ou page fetchée). Les calculs sont dérivés de formules sourcées et sont marqués [CALCUL DÉRIVÉ]. Rien n'est estimé « au jugé ».

---

## 1. Arrhenius / facteur d'accélération thermique

### 1.1 Formule

> « AF = (tu/tt) = exp[Ea/k × (1/Tu − 1/Tt)] », avec « Ea is the apparent activation energy (eV); k is Boltzmann's constant (8.62 × 10⁻⁵ eV/K) »
**[MODÈLE]** — JEDEC, *Arrhenius equation (for reliability)*, dictionnaire officiel : https://www.jedec.org/standards-documents/dictionary/terms/arrhenius-equation-reliability
*Réserve d'honnêteté* : cette page a renvoyé **HTTP 403** en fetch direct ; la formule m'est parvenue via l'index de recherche pointant sur cette URL. Elle est identique à celle que j'ai lue en clair dans les sources NASA ci-dessous.

### 1.2 Valeurs d'Ea sourcées

| Mécanisme | Ea | Source |
|---|---|---|
| Électromigration (EaEM) | **0,8 eV**, avec **n = 2** | NASA NEPP/JPL |
| TDDB (EaTDDB) | **0,75 eV** | NASA NEPP/JPL |
| EM — diffusion joints de grains (Al) | **0,7 eV** | Springer/ifte |
| EM — diffusion de surface (Cu) | **0,8 eV** (table) / **0,9 eV** (texte, mécanisme dominant) | Springer/ifte |
| EM — diffusion en volume | Al **1,2 eV** / Cu **2,3 eV** | Springer/ifte |

Citation exacte NASA (PDF lu, `pdftotext`) :
> « λEM = λTDDB = λHCD, Tj =