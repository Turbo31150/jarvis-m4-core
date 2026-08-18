#!/usr/bin/env bash
# Benchmark massif LM Studio — charge chaque modèle SEUL, réglages optimisés,
# mesure chargement/latence/débit/qualité. Restaure qwen à la fin.
export PATH="$HOME/.lmstudio/bin:$PATH"
BASE="http://127.0.0.1:11235/v1/chat/completions"
OUT=~/jarvis/data/serie/lms_bench_massif_$(date +%Y%m%d_%H%M%S).json
CTX=8192; PAR=1
MODELS=("google/gemma-4-e4b" "qwen/qwen3.5-9b" "google/gemma-4-12b-qat" "openai/gpt-oss-20b" "google/gemma-4-26b-a4b-qat")

python3 - "$BASE" "$OUT" "$CTX" "$PAR" "${MODELS[@]}" <<'PY' &
import sys,json,time,subprocess,urllib.request
base,out,ctx,par=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]
models=sys.argv[5:]
import os
env=dict(os.environ); env["PATH"]=os.path.expanduser("~/.lmstudio/bin")+":"+env.get("PATH","")
def sh(c,t=240):
    return subprocess.run(c,shell=True,capture_output=True,text=True,env=env,timeout=t)
# prompts de qualité (calcul / code / langue+raisonnement)
PROMPTS=[
 ("calc","Combien font 17 x 23 ? Réponds juste par le nombre.","391"),
 ("code","Écris UNE ligne Python qui inverse la chaîne s. Réponds juste le code.","[::-1]"),
 ("fr","Traduis en anglais: 'Le chat dort sur le canapé.' Réponds juste la traduction.","couch"),
]
def ask(model,q,mx=160):
    msgs=[{"role":"user","content":q},{"role":"assistant","content":"<think>\n\n</think>\n\n"}]
    body=json.dumps({"model":model,"messages":msgs,"max_tokens":mx,"temperature":0.2,"stream":False}).encode()
    req=urllib.request.Request(base,body,{"Content-Type":"application/json"})
    t=time.time()
    try:
        j=json.load(urllib.request.urlopen(req,timeout=90)); dt=time.time()-t
        m=j["choices"][0]["message"]
        c=(m.get("content") or "").strip() or (m.get("reasoning_content") or "").strip()
        ct=j.get("usage",{}).get("completion_tokens",0)
        return dt,ct,c
    except Exception as e:
        return None,0,"ERR:"+str(e)[:60]
results={}
for M in models:
    print(f"\n########## {M} ##########",flush=True)
    sh("lms unload --all",60)
    time.sleep(2)
    t0=time.time()
    r=sh(f'lms load "{M}" -c {ctx} --gpu max --parallel {par} --ttl 3600 -y',300)
    load_s=round(time.time()-t0,1)
    loaded = r.returncode==0 and "error" not in (r.stderr+r.stdout).lower()
    print(f"load rc={r.returncode} en {load_s}s loaded={loaded}",flush=True)
    if not loaded:
        results[M]={"loaded":False,"load_s":load_s,"err":(r.stderr or r.stdout)[-200:]}
        print("  ÉCHEC:",(r.stderr or r.stdout)[-160:],flush=True)
        continue
    time.sleep(1)
    # warmup court + 3 prompts
    ask(M,"ok?",20)
    lat=[]; toks=[]; score=0; samples=[]
    for name,q,expect in PROMPTS:
        dt,ct,c=ask(M,q)
        if dt: lat.append(dt); toks.append(ct/dt if dt else 0)
        good = expect.lower() in (c or "").lower()
        if good: score+=1
        samples.append({"p":name,"ok":good,"dt":round(dt,1) if dt else None,"txt":c[:80]})
        print(f"  [{name}] {'✅' if good else '⚠️'} {round(dt,1) if dt else 'ERR'}s :: {c[:70]}",flush=True)
    avg_lat=round(sum(lat)/len(lat),2) if lat else None
    avg_tps=round(sum(toks)/len(toks),1) if toks else 0
    results[M]={"loaded":True,"load_s":load_s,"avg_lat_s":avg_lat,"avg_tok_s":avg_tps,
                "quality":f"{score}/3","samples":samples}
    print(f"  => load={load_s}s lat={avg_lat}s tok/s={avg_tps} qualité={score}/3",flush=True)
json.dump({"ctx":int(ctx),"parallel":int(par),"results":results},open(out,"w"),ensure_ascii=False,indent=1)
# restaure qwen (défaut stable) context raisonnable
sh("lms unload --all",60); time.sleep(1)
sh('lms load "qwen/qwen3.5-9b" -c 16384 --gpu max --parallel 2 --ttl 1800 -y',180)
print("\n===== CLASSEMENT =====",flush=True)
ok={k:v for k,v in results.items() if v.get("loaded")}
rank=sorted(ok.items(),key=lambda kv:(-int(kv[1]["quality"][0]), kv[1]["avg_lat_s"] or 99))
for i,(k,v) in enumerate(rank,1):
    print(f"{i}. {k:30} qual={v['quality']} lat={v['avg_lat_s']}s {v['avg_tok_s']}tok/s load={v['load_s']}s",flush=True)
print(f"\nJSON: {out}",flush=True)
print("qwen rechargé (16k/parallel2) comme défaut stable.",flush=True)
PY
echo "PID bench: $!"