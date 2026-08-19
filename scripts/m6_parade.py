#!/usr/bin/env python3
"""m6_parade — un seul endroit pour parler aux modeles qwen du parc.

POURQUOI CE MODULE EXISTE
Les modeles qwen3 / qwen3.5 servis par LM Studio rangent tout leur raisonnement
dans `reasoning_content` et laissent `content` VIDE sur /v1/chat/completions.
Mesure du 19/08/2026 sur qwen3-4b : content = 0 caractere, reasoning = 677.
Un appelant naif recoit donc une chaine vide, sans erreur, sans code de retour
non nul — la panne est parfaitement muette.

Augmenter max_tokens ne corrige rien (essaye : 2500 tokens dans jarvis-table-ronde,
le content restait vide). La parade qui marche est de fermer <think> D AVANCE sur
/v1/completions : le modele n a plus de phase de raisonnement a remplir et repond
directement. Verifie sur qwen3-4b et qwen3.5-9b.

USAGE
    from m6_parade import ask
    texte = ask("Ta question")                  # cascade M6 -> hub -> Ollama local
    texte = ask("...", modele="qwen/qwen3-4b")  # modele impose

`ask` leve M6Muet si AUCUN backend ne rend de contenu. Elle ne rend JAMAIS une
chaine vide en pretendant avoir reussi.
"""

import json, os, urllib.request

BACKENDS = [
    ("M6-cable",  "http://10.42.0.230:1234",     "completions"),
    ("M6-tailsc", "http://100.112.114.32:1234",  "completions"),
    ("hub",       "http://127.0.0.1:18800",      "chat"),
    ("ollama-M4", "http://127.0.0.1:11434",      "ollama"),
]
DEFAUT_OLLAMA = os.environ.get("M6_PARADE_OLLAMA", "qwen2.5:7b")


class M6Muet(RuntimeError):
    """Aucun backend n a rendu de contenu. A remonter, jamais a avaler."""


def _post(url, corps, timeout):
    req = urllib.request.Request(url, data=json.dumps(corps).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _modele(base, timeout=6):
    try:
        with urllib.request.urlopen(base + "/v1/models", timeout=timeout) as r:
            ids = [m["id"] for m in json.load(r).get("data", []) if "embed" not in m["id"]]
        return ids[0] if ids else None
    except Exception:
        return None


def ask(prompt, modele=None, max_tokens=900, temperature=0.3, timeout=300):
    """Retourne le TEXTE du modele. Leve M6Muet si tous les backends sont muets."""
    erreurs = []
    for nom, base, forme in BACKENDS:
        try:
            if forme == "completions":
                mod = modele or _modele(base)
                if not mod:
                    erreurs.append(f"{nom}:pas de modele"); continue
                d = _post(base + "/v1/completions", {
                    "model": mod,
                    # <think></think> ferme d avance : c est TOUTE la parade.
                    "prompt": f"<|im_start|>user\n{prompt}<|im_end|>\n"
                              f"<|im_start|>assistant\n<think></think>\n\n",
                    "max_tokens": max_tokens, "temperature": temperature,
                    "stop": ["<|im_end|>"]}, timeout)
                t = ((d.get("choices") or [{}])[0].get("text") or "").strip()
            elif forme == "chat":
                d = _post(base + "/v1/chat/completions", {
                    "model": modele or "jarvis-quality",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens, "temperature": temperature}, timeout)
                m = (d.get("choices") or [{}])[0].get("message", {})
                t = (m.get("content") or "").strip()
                if not t:
                    # le hub peut fronter un modele a raisonnement : on etiquette
                    r = (m.get("reasoning_content") or "").strip()
                    t = f"[{nom} — raisonnement brut, conclusion non emise]\n{r[-1200:]}" if r else ""
            else:
                d = _post(base + "/api/generate", {
                    "model": modele or DEFAUT_OLLAMA, "prompt": prompt, "stream": False,
                    "keep_alive": "5m",
                    "options": {"temperature": temperature, "num_predict": max_tokens}}, timeout)
                t = (d.get("response") or "").strip()
            if t:
                return t
            erreurs.append(f"{nom}:vide")
        except Exception as e:
            erreurs.append(f"{nom}:{type(e).__name__}")
    raise M6Muet("aucun backend n a rendu de contenu — " + ", ".join(erreurs))


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Reponds par le seul mot : operationnel."
    try:
        print(ask(q, max_tokens=120))
    except M6Muet as e:
        print(f"m6_parade: {e}", file=sys.stderr); sys.exit(1)
