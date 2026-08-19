[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — VERIFICATION ADVERSARIALE.
Un agent explorateur pretend ceci (axe mcp-tools):
  chemin: /home/pamerys/jarvis/mcp/omega_gateway.py
  role pretendu: Passerelle MCP : agrege N serveurs stdio derriere un seul endpoint HTTP
  commande pretendue: sed -n '1,12p' /home/pamerys/jarvis/mcp/omega_gateway.py ; wc -l
  preuve fournie: 298 lignes, stdlib uniquement. Docstring: 'Les serveurs enfants sont demarres a la demande et gardes chauds ; un enfant mort est relance au prochain appel'. Code: 'def appel(...): if not self._vivant(): self._demarrer()' puis relance unique sur RuntimeError/TimeoutError/BrokenPipeError.

Ta mission est de REFUTER. Par defaut, considere que c'est FAUX jusqu'a preuve du contraire.
1. Le fichier existe-t-il vraiment ? (ls -la, file)
2. Fait-il vraiment ce qui est pretendu ? Lis-le REELLEMENT (cat / sed -n). Ne te

[assistant] The code matches. Now let me verify the claimed command, check for hardcoded fallbacks, and confirm the stdlib-only claim.

[assistant] J'ai tenté de réfuter sur les 4 axes demandés. Échec de la réfutation : chaque élément est vérifié.

**1. Existence** — `/home/pamerys/jarvis/mcp/omega_gateway.py`, `-rw-rw-r-- 1 pamerys pamerys 10443 août 18 00:31`, `file` → `Python script, Unicode text, UTF-8 text executable`. `wc -l` → **298** (exact).

**2. Rôle réel** (lecture intégrale) — conforme. Docstring l.4 : `Agrège N serveurs MCP stdio derrière UN seul endpoint HTTP (Streamable HTTP).` Mécanique confirmée : classe `Passerelle` (l.110-140) charge `mcpServers`, **écarte** les serveurs HTTP (l.118 `if spec.get("type") in ("sse","streamableHttp") or "url" in spec: continue`) donc bien stdio uniquement ; préfixage l.128 `copie["name"] = f"{court}{SEP}{o['name']}"` avec `SEP = "__"` ; serveur HTTP l.294 `Serveur(("127.0.0.1", args.port), Handler).serve_forever()` avec routes `POST /mcp` (l.202) et `GET /sante` (l.195).

**3. Preuve citée** — fidèle. Docstring l.9-10 : `Les serveurs enfants sont démarrés à la demande / et gardés chauds ; un enfant mort est relancé au prochain appel, jamais masqué.` (l'explorateur a tronqué `, jamais masqué`, sans altérer le sens). Code l.88-97 exactement :
```python
def appel(self, methode: str, params: dict | None = None):
    with self.verrou:
        if not self._vivant():
            self._demarrer()
        try:
            return self._appel_brut(methode, params)
        except (RuntimeError, TimeoutError, BrokenPipeError):
            # Une relance, une seule : si ça retombe, l'e