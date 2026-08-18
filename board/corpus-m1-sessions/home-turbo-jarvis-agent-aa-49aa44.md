[user] Tu implémentes UNE tâche précise dans un fichier Python existant. Tu ne connais rien de la conversation qui précède : tout ce dont tu as besoin est ci-dessous.

## Le contexte

`/home/turbo/jarvis/board/board.py` est un CLI Python (stdlib seule, pas de dépendances) qui fait tourner un « board d'experts » local : un corpus de documents est découpé en *chunks* stockés dans SQLite (`/home/turbo/jarvis/board/board.db`), vectorisés via un serveur d'embeddings local, puis interrogé.

Lis le fichier en entier avant de commencer. Il fait ~370 lignes.

Le serveur d'embeddings est LM Studio sur `http://127.0.0.1:1234/v1/embeddings`, modèle `text-embedding-nomic-embed-text-v1.5`, dimension **768** (constatée, ne la suppose pas ailleurs).

État actuel de la base : 40 633 chunks, dont 3 231 vectorisés.

## Le problème à résoudre

Lors d'un lot de vectorisation, **231 chunks sur 250 ont réussi et 19 ont échoué sans laisser aucune trace**. La fonction `embed()` renvoie `None` pour toute erreur, ce qui rend les échecs indistinguables : timeout réseau ? texte trop long refusé par le modèle ? dimension inattendue ? erreur HTTP ? On ne sait pas, et on ne peut pas décider quoi faire.

## Ce que tu dois implémenter — exactement ceci, rien de plus

**1. Rendre les échecs d'`embed()` diagnosticables.**
`embed()` doit distinguer et remonter la CAUSE de l'échec plutôt qu'un `None` muet. Les causes à distinguer au minimum : timeout, erreur HTTP (avec le code), réponse illisible/inattendue, dimension d

[assistant] Ruff stripped the imports added before their usage (known trap). Re-adding now that they're used.

[assistant] Done. All verifications real and passing.

## 1. Diff

`board/` is untracked in git (`?? board/`), so there is no baseline for `git diff` — here is the change by hand. **No file was committed.**

**Imports** (+2): `socket`, `subprocess`. **Constant** (+1): `GPU_TEMP_MAX = 89`.

```diff
-def embed(text: str) -> list[float] | None:
-    try:
-        v = _post("/embeddings", {...})["data"][0]["embedding"]
-    except Exception:
-        return None
-    if len(v) != EMBED_DIM:
-        print(f"  ! dimension {len(v)} != {EMBED_DIM} attendue — vecteur rejete")
-        return None
-    return v
+class Embedding(list):          # sous-classe de list : un echec reste falsy
+    __slots__ = ("cause", "detail")   # mais porte sa cause
+
+def embed(text: str, tentatives: int = 2) -> Embedding:
+    # HTTPError -> http_<code> · socket.timeout / URLError(timeout) -> timeout
+    # URLError autre -> reseau · schema/JSON casse -> reponse_illisible
+    # len != 768 -> dimension
+    # reessai UNIQUE, et seulement si transitoire (timeout/reseau/http_5xx)
+
+def gpu_temp_max() -> int | None:   # nvidia-smi ; None si absent/illisible
```

```diff
 def cmd_embed(limit=None, batch=100):
-    ok = depuis_commit = 0
-    with ThreadPoolExecutor(max_workers=4) as pool:
-        for n, (r, v) in enumerate(zip(rows, pool.map(...,  rows)), 1):
-            if v: ...; depuis_commit += 1
-            if depuis_commit >= batch: c.commit(); ...
-    print(f"✓ {ok}/{len(rows)} vectorises")
+    ok = trai