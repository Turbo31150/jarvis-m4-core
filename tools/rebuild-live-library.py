#!/usr/bin/env python3
import csv, hashlib, json, os, re, shutil, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/pamerys/labo/bibliotheque/rebuild-20260814")
ROOT.mkdir(parents=True, exist_ok=True)
SESSION_ROOTS = [("m4", Path("/home/pamerys/.claude/dot-claude/projects")), ("m1-archive", Path("/home/pamerys/m1-disk/.claude/projects"))]
LIB_ROOTS = [Path("/home/pamerys/labo/bibliotheque"), Path("/home/pamerys/m1-disk/labo/bibliotheque"), Path("/home/pamerys/jarvis/bibliotheque"), Path("/home/pamerys/m1-disk/jarvis/bibliotheque")]
STOP = set("a au aux avec ce ces cette dans de des du en et est été faire for from il ils je la le les leur lui mais me mes mon ne nos notre nous on ou par pas pour que qui quoi se ses son sur ta te tes toi ton tu un une vos votre vous y the and are as at be by can do for from has have how if in is it me my no not of on or our so that the their there this to was we what when where which who why will with you your from into via then than also have dont donc une des les pour avec sans sous entre cette cet cette être faire fait plus moins comme après avant tout tous aux ses son sont dans par sur chez alors lorsque quand mais car qui que quoi comment pourquoi comment use using from with into api code test tests build bug fix setup config configuration server service docker redis swarm mcp cdp browser chrome claude gemini codex jarvis turbo".split())
TOKEN = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_-]{3,}")
SECRET = re.compile(r"(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_\-]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}|AIza[0-9A-Za-z_-]{20,}|Bearer\s+[A-Za-z0-9._-]{12,})", re.I)

def text_of(message):
    if isinstance(message, str): return message
    if isinstance(message, dict): return text_of(message.get("content", ""))
    if isinstance(message, list):
        return " ".join(text_of(x.get("text", x) if isinstance(x, dict) else x) for x in message)
    return ""

def keywords(text):
    text = SECRET.sub(" ", text)
    out = []
    for token in TOKEN.findall(text.lower()):
        token = token.strip("_- ")
        if token in STOP or token.isdigit() or len(token) < 4: continue
        out.append(token[:48])
    return Counter(out)

def scan(root_label, root):
    stats = Counter(); global_kw = Counter(); rows = []
    if not root.exists(): return stats, global_kw, rows
    for path in root.rglob("*.jsonl"):
        stats["files"] += 1; stats["bytes"] += path.stat().st_size
        sid = path.stem; cwd = ""; first_ts = ""; last_ts = ""; users = assistants = lines = 0; chars = 0; kws = Counter()
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for raw in fh:
                    lines += 1
                    try: obj = json.loads(raw)
                    except Exception: continue
                    sid = obj.get("sessionId") or sid
                    ts = obj.get("timestamp") or ""
                    if ts and not first_ts: first_ts = ts
                    if ts: last_ts = ts
                    cwd = cwd or str(obj.get("cwd") or "")
                    typ = obj.get("type")
                    if typ == "user":
                        users += 1; txt = text_of(obj.get("message", obj.get("content", ""))); chars += len(txt); c = keywords(txt); kws.update(c); global_kw.update(c)
                    elif typ == "assistant": assistants += 1
        except OSError: stats["errors"] += 1; continue
        top = ",".join(f"{k}:{v}" for k,v in kws.most_common(20))
        rows.append([root_label, sid, str(path), str(path.stat().st_size), first_ts, last_ts, cwd, str(lines), str(users), str(assistants), str(chars), top])
        stats["user_messages"] += users; stats["assistant_messages"] += assistants; stats["lines"] += lines; stats["chars"] += chars
    return stats, global_kw, rows

all_rows = []; total = Counter(); all_kw = Counter()
for label, root in SESSION_ROOTS:
    st, kw, rows = scan(label, root); total.update(st); all_kw.update(kw); all_rows.extend(rows); print("{}: files={} bytes={} lines={} user={}".format(label, st["files"], st["bytes"], st["lines"], st["user_messages"]), flush=True)

with (ROOT / "CLAUDE_SESSIONS.tsv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["source","session_id","path","bytes","first_timestamp","last_timestamp","cwd","lines","user_messages","assistant_messages","user_chars","keywords"]); w.writerows(all_rows)
with (ROOT / "CLAUDE_KEYWORDS.tsv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["keyword","occurrences","sessions"]); session_counts = Counter()
    for row in all_rows:
        for pair in row[-1].split(","):
            if ":" in pair:
                k, n = pair.rsplit(":", 1); session_counts[k] += 1
    for k,n in all_kw.most_common(): w.writerow([k,n,session_counts[k]])

index = ROOT / "BLOCS-INDEX.tsv"; seen = set(); out = ["nom\tsource\tdanger\tbloc"]
def add(line):
    c = line.rstrip("\n").split("\t")
    if len(c) < 4 or c[0] == "nom": return
    key = (c[0], c[1])
    if key in seen: return
    seen.add(key); out.append("\t".join(c[:4]))
for base in LIB_ROOTS:
    for p in base.rglob("*-blocs.tsv") if base.exists() else []:
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines(): add(line)
        except OSError: pass
old = Path("/home/pamerys/labo/bibliotheque/lib/BLOCS-INDEX.tsv")
if old.exists():
    for line in old.read_text(encoding="utf-8", errors="replace").splitlines(): add(line)
for k,n in all_kw.most_common():
    add(f"claude-keyword-{hashlib.sha1(k.encode()).hexdigest()[:12]}\tclaude-sessions\t🟢\t{k} — {n} occurrences dans les sessions Claude indexées")
index.write_text("\n".join(out) + "\n", encoding="utf-8")
summary = ROOT / "REBUILD-REPORT.md"
summary.write_text("# Reconstruction bibliothèque vivante — 2026-08-14\n\n- Sessions indexées : {}\n- Fichiers JSONL : {}\n- Lignes relues : {}\n- Messages utilisateur : {}\n- Messages assistant : {}\n- Caractères utilisateur analysés : {}\n- Mots-clés : {}\n- Blocs dédupliqués : {}\n\nLes conversations brutes ne sont pas copiées. Les secrets détectables sont exclus de l’extraction.\n".format(len(all_rows), total["files"], total["lines"], total["user_messages"], total["assistant_messages"], total["chars"], len(all_kw), len(out)-1), encoding="utf-8")
print(f"done sessions={len(all_rows)} keywords={len(all_kw)} blocks={len(out)-1}", flush=True)
