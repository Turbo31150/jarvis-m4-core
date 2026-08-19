# -*- coding: utf-8 -*-
"""Harvest prospection 19/08/2026 — scoring DETERMINISTE (0 token, 0 inference)."""
import csv, json, datetime, re

TODAY = datetime.date(2026, 8, 19)
B = "https://www.free-work.com"

# (titre, societe, lieu, tjm_min, tjm_max, date_pub, url, source)
M = [
 ("Expert IA Agentique Senior — systemes multi-agents, MCP, orchestration","Hexateam","Ile-de-France",None,None,"2026-08-16","/fr/tech-it/job-mission/chef-de-projet-systemes-et-reseaux/expert-ia-agentique-senior-h-f-systemes-multi-agents-mcp-orchestration","free-work/agent-ia+rag"),
 ("Expert IA generative / LLM Engineer — Cybersecurite","DATAMED RESEARCH","Toulouse, Occitanie",400,500,"2026-08-06","/fr/tech-it/job-mission/consultant-cyber-securite/expert-ia-generative-llm-engineer-cybersecurite","free-work/ia-generative"),
 ("Ingenieur Orchestration et Automatisation Reseau (n8n, API)","CELAD","Toulouse, Occitanie",360,420,"2026-07-31","/fr/tech-it/job-mission/ingenieur-apres-vente/ingenieur-orchestration-et-automatisation-reseau-h-f","free-work/n8n"),
 ("Developpeur IA Agents & Orchestration H/F","Freelance.com","Ile-de-France",510,590,"2026-08-14","/fr/tech-it/job-mission/developpeur-autre-langage-cobol-perl-vba-ruby-shell/developpeur-ia-agents-orchestration-h-f","free-work/rag"),
 ("Expert IA generative et Plateforme IA H/F","Freelance.com","Ile-de-France",510,590,"2026-08-14","/fr/tech-it/job-mission/expert-seo-consultant-referencement/expert-ia-generative-et-plateforme-ia-h-f","free-work/rag+ia-generative"),
 ("Consultant IA Generative / Claude (Anthropic)","SMARTPOINT","Ile-de-France",500,600,"2026-08-17","/fr/tech-it/job-mission/consultant/consultant-ia-generative-claude-anthropic","free-work/rag+ia-generative"),
 ("Chef de Projet IA agentique — gouvernance et archi Data","ARDEMIS PARTNERS","Paris",400,500,"2026-08-18","/fr/tech-it/job-mission/assistant-chef-de-projet/chef-de-projet-ia-agentique-gouvernance-et-archi-data","free-work/agent-ia"),
 ("Architecte Data XP IA Agentique","ARDEMIS PARTNERS","Paris",400,580,"2026-08-17","/fr/tech-it/job-mission/architecte-de-base-de-donnees/architecte-data-xp-ia-agentique","free-work/agent-ia"),
 ("Expert IA Generative — Agents IA, Copilot et Industrialisation","AVA2I","Ile-de-France",None,None,"2026-08-13","/fr/tech-it/job-mission/expert-seo-consultant-referencement/expert-ia-generative-agents-ia-copilot-et-industrialisation","free-work/agent-ia+rag"),
 ("Data & AI Engineer Senior (H/F)","Freelance.com","Bois-Colombes, Ile-de-France",400,580,"2026-08-17","/fr/tech-it/job-mission/data-engineer/data-ai-engineer-senior-h-f","free-work/agent-ia+ia-generative"),
 ("Tech Lead IA — CIB (H/F)","STORM GROUP","Ile-de-France",400,650,"2026-08-17","/fr/tech-it/job-mission/lead-developer/tech-lead-ia-cib-h-f","free-work/ia-generative"),
 ("Data Scientist specialise evaluation des LLMs","ISUPPLIER","Ile-de-France",400,550,"2026-08-17","/fr/tech-it/job-mission/data-scientist/data-scientist-specialise-dans-levaluation-des-llms","free-work/ia-generative"),
 ("Consultant IA - SDLC/DevEx","FF","Paris",None,None,"2026-08-16","/fr/tech-it/job-mission/consultant/consultant-ia-sdlc-devex","free-work/agent-ia"),
 ("Developpeur Python Flask & Automatisation STB","R&S TELECOM","Meudon, Ile-de-France",None,None,"2026-08-16","/fr/tech-it/job-mission/developpeur-python/developpeur-python-flask-automatisation-stb","free-work/agent-ia+automatisation"),
 ("Ingenieur automation broadcast ST2110","INSYCO","Paris",500,600,"2026-08-18","/fr/tech-it/job-mission/ingenieur-apres-vente/ingenieur-automation-broadcast-serveurs-et-infrastructures-de-diffusion-st2110","free-work/automatisation"),
 ("Architecte Applicatif — Audit & Urbanisation (H/F)","CAT-AMANIA","Centre-Val de Loire",None,None,"2026-08-18","/fr/tech-it/job-mission/administrateur-applicatif-erp-crm-sirh/architecte-applicatif-audit-urbanisation-h-f","free-work/agent-ia"),
 ("Expert Methode & IA","INFOTEL CONSEIL","Saint-Herblain",300,470,"2026-08-11","/fr/tech-it/job-mission/expert-seo-consultant-referencement/expert-methode-ia","free-work/agent-ia"),
 ("Testeur & automatisation - Azure DevOps","PROPULSE IT","Le Plessis-Robinson, Ile-de-France",225,450,"2026-08-17","/fr/tech-it/job-mission/ingenieur-devops-cloud/testeur-automatisation-azure-devops-45","free-work/automatisation"),
 ("Ingenieur Automatisation DevOps","LeHibou","Guyancourt, Ile-de-France",550,550,"2026-08-12","/fr/tech-it/job-mission/ingenieur-devops-cloud/ingenieur-automatisation-devops-2","free-work/automatisation"),
 ("Ingenieur DevOps / SRE Windows et automatisation","LeHibou","Paris",750,750,"2026-08-11","/fr/tech-it/job-mission/ingenieur-devops-cloud/ingenieur-devops-sre-oriente-systemes-windows-et-automatisation","free-work/automatisation"),
 ("Architecte & Expert Technique IA & DATA","VISIAN","Paris",600,800,"2026-07-21","/fr/tech-it/job-mission/expert-e-protection-donnees/architecte-expert-technique-ia-data","free-work/n8n"),
 ("Data Scientist / Expert IA Generative — Senior Claude (H/F)","Nicholson SAS","Nanterre, Ile-de-France",650,650,"2026-07-27","/fr/tech-it/job-mission/data-scientist/295-data-scientist-expert-ia-generative-senior-claude-h-f","free-work/rag"),
]

KW = ["agent","agentique","multi-agents","mcp","orchestration","n8n","rag","llm","ia generative",
      "automatisation","automation","claude","anthropic","plateforme ia","python"]

def norm(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")

def score(m):
    titre, soc, lieu, tmin, tmax, dpub, url, src = m
    d = datetime.date.fromisoformat(dpub); age = (TODAY - d).days
    s_frais = 3.0 if age <= 7 else (1.5 if age <= 14 else 0.0)
    L = norm(lieu)
    s_geo = 3.0 if ("toulouse" in L or "occitanie" in L) else (1.5 if ("ile-de-france" in L or "paris" in L) else 0.5)
    tj = tmax or tmin
    s_tjm = 0.8 if tj is None else (2.0 if tj >= 600 else 1.7 if tj >= 500 else 1.3 if tj >= 400 else 0.5)
    T = norm(titre)
    hits = sorted({k for k in KW if norm(k) in T})
    s_tec = min(2.0, 0.4 * len(hits))
    return round(s_frais + s_geo + s_tjm + s_tec, 2), age, hits, s_frais, s_geo, s_tjm, s_tec

rows = []
for m in M:
    sc, age, hits, a, b_, c, d_ = score(m)
    titre, soc, lieu, tmin, tmax, dpub, url, src = m
    rows.append(dict(score=sc, titre=titre, societe=soc, lieu=lieu,
        tjm=(f"{tmin}-{tmax} EUR/j" if tmin and tmax and tmin != tmax else (f"{tmin} EUR/j" if tmin else "n.c.")),
        date_pub=dpub, age_jours=age, frais=("OUI" if age <= 7 else "non"),
        mots_cles=";".join(hits), detail=f"frais={a} geo={b_} tjm={c} techno={d_}",
        url=B + url, source=src))
rows.sort(key=lambda r: (-r["score"], r["age_jours"]))

with open("harvest_20260819.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open("harvest_20260819.json", "w", encoding="utf-8") as f:
    json.dump({"date": str(TODAY), "sources_ratissees": [
        "free-work/n8n","free-work/agent-ia","free-work/rag","free-work/ia-generative",
        "free-work/automatisation","codeur.com (0 resultat pertinent)"],
        "missions": rows}, f, ensure_ascii=False, indent=2)

print(f"{len(rows)} missions retenues | fraiches (<=7j) : {sum(1 for r in rows if r['frais']=='OUI')}")
print(f"Toulouse/Occitanie : {sum(1 for r in rows if 'oulouse' in r['lieu'] or 'ccitanie' in r['lieu'])}")
print(f"TJM >= 400 affiche : {sum(1 for r in rows if r['tjm']!='n.c.')}\n")
print("%-5s %-3s %-58s %-22s %-30s %s" % ("SCORE","AGE","MISSION","SOCIETE","LIEU","TJM"))
for r in rows[:12]:
    print("%-5s %-3s %-58s %-22s %-30s %s" % (r["score"], r["age_jours"], r["titre"][:58], r["societe"][:22], r["lieu"][:30], r["tjm"]))
