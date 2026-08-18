[user] ## Adversarial Claim Verifier (voter 3/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Contrôle des ventilateurs, du refroidissement AIO et de l'éclairage RGB thermique sous Linux sur une carte mère MSI B550-A PRO (MS-7C56, Super I/O NCT6687D, BIOS A.L1, Ryzen, Ubuntu kernel 6.8).

Contexte matériel vérifié sur la machine :
- Module nct6687 (DKMS Fred78290/nct6687d) chargé, expose 8 canaux fan/pwm + 7 températures. dmesg : "active fan config=default, NCT6687D EC firmware version 1.0 build 05/07/20".
- Pompe de l'AIO sur PUMP_FAN1 : 3498 RPM, fonctionne.
- CPU_FAN1 : 0 RPM alors que pwm1 est à 74 % — aucun ventilateur branché sur ce header.
- Ventilateurs de boîtier sur SYS_FAN : 766 / 1268 / 1657 RPM. CPU à 65-70 °C.
- Forcer tous les PWM à 100 % ne fait gagner que 2 °C (69 → 67).
- Contrôleur RGB : device USB 1462:7c56 "MSI MYSTIC LIGHT", toujours présent.
- liquidctl ne détecte AUCUN AIO (pas d'interface USB sur ce watercooling).
- RÉGRESSION OBSERVÉE : l'éclairage RGB des ventilateurs était configuré en mode température (rouge = chaud, vert = froid) ; il s'est ÉTEINT au moment où fancontrol a passé les pwm_enable de 2 (firmware) à 1 (manuel). Le contrôle a été rendu au firmware (pwm_enable=2) et fancontrol désactivé.

Trois axes à couvrir, avec des sources vérifiables (documentation projet, issues GitHub, wikis Arch/Gentoo, forums utilisateurs) :

AXE 1 — RGB thermique et contrôle ventilo peuvent-ils coexister ?
Le passage des PW

[assistant] PR #87 linkage confirmed. Let me check the raw README and the PR diff for exact provenance.

[assistant] All three elements verified directly against the GitHub API (primary source, not a rendered page).