[user] Trouve la CAUSE RACINE d'un service systemd user qui ne démarre jamais sur cette machine (M1, Ubuntu, hôte turbo-MS-7C56). N'applique AUCUN correctif définitif : ta mission est le diagnostic. Tu peux lancer des processus de test isolés et les tuer.

PROBLÈME
`browseros-mcp.service` (systemd --user) échoue systématiquement. Son script d'amorçage `/home/turbo/jarvis/bin/browseros-mcp-up.sh` attend 60 s un endpoint DevTools sur le port CDP 9105 puis abandonne avec :

    [browseros-mcp] CDP :9105 sans endpoint DevTools après 60s.
    Le navigateur peut tourner SANS exposer de CDP : vérifier
    ~/.config/browser-os/DevToolsActivePort — absent = aucun port ouvert

Le navigateur `browseros.service` (systemd --user) tourne pourtant, lancé par :
    /usr/lib/browseros/browseros --no-first-run --no-default-browser-check --remote-debugging-port=9105 --remote-allow-origins=* http://127.0.0.1:9200

Version : `BrowserOS 146.0.7818.31` (base Chromium 146).

FAITS DÉJÀ ÉTABLIS — ne les re-teste pas, pars de là
- Le processus tourne bien AVEC le flag `--remote-debugging-port=9105` (vérifié par ps).
- Le port 9105 n'est JAMAIS ouvert (ss -ltn).
- Aucun fichier `DevToolsActivePort` dans `/home/turbo/.config/browser-os/` (son user-data-dir par défaut).
- HYPOTHÈSE DÉJÀ RÉFUTÉE : « Chromium ≥136 ignore --remote-debugging-port sur le profil par défaut ». Test isolé fait avec un `--user-data-dir` explicite tout neuf et le port 9107 → `DevToolsActivePort` toujours ABSENT après 40 s. Ce n'est donc 

[assistant] I'll start by gathering the concrete evidence on the binary, the running processes, and the policies.

[assistant] The DevTools code is compiled in but never starts. Let me test the pipe transport to isolate the port path.

[assistant] Strong lead: startup stalls right after OSCrypt selects GNOME_LIBSECRET. Testing the keyring hypothesis.

[assistant] DevTools **works** with `--password-store=basic`. Now characterizing why libsecret blocks.

[assistant] Diagnostic terminé. Instance de production intacte (PID 78750), tous les processus de test tués.

## 1. CAUSE RACINE

**Le navigateur ne « n'ouvre pas de CDP » : il ne finit jamais son démarrage.** Il se bloque indéfiniment dans l'initialisation d'OSCrypt sur le backend `GNOME_LIBSECRET`, parce que le trousseau `login` de gnome-keyring est **verrouillé**. Le serveur DevTools HTTP démarre plus tard dans la séquence (`PostBrowserStart`) — il n'est donc jamais atteint.

### Preuve causale (test A/B, même binaire, même profil neuf)

| Test | Commande (extrait) | Résultat |
|---|---|---|
| test1 | `--user-data-dir=/tmp/…/udd1 --remote-debugging-port=9107` (backend auto = libsecret) | aucune ligne `DevTools listening`, blocage 25 s |
| test4 | `--password-store=gnome-libsecret --remote-debugging-port=9109` | `grep -c "DevTools listening"` → **0** |
| **test3** | `--password-store=basic --remote-debugging-port=9107` | **`DevTools listening on ws://127.0.0.1:9107/devtools/browser/4370e095-…`** à ~1 s |

Le **seul** paramètre changé est le backend de stockage de mots de passe.

### Preuve de l'état du trousseau
```
gdbus call --session --dest org.freedesktop.secrets \
  --object-path /org/freedesktop/secrets/collection/login \
  --method org.freedesktop.DBus.Properties.Get org.freedesktop.Secret.Collection Locked
→ (<true>,)          # collection "login" VERROUILLÉE
→ (<false>,)         # collection "session" (volatile) déverrouillée
```
Le service Secret répond (gnome-keyring-daemon 