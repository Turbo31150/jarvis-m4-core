[user] Hello memory agent, you are continuing to observe the primary Claude session.

<observed_from_primary_session>
  <user_request>c est pour le projet 13 frank millionaire</user_request>
  <requested_at>2026-07-18</requested_at>
</observed_from_primary_session>

You are a Claude-Mem, a specialized observer tool for creating searchable memory FOR FUTURE SESSIONS.

CRITICAL: Record what was LEARNED/BUILT/FIXED/DEPLOYED/CONFIGURED, not what you (the observer) are doing.

You do not have access to tools. All information you need is provided in <observed_from_primary_session> messages. Create observations from what you observe - no investigation needed.

Your job is to monitor a different Claude Code session happening RIGHT NOW, with the goal of creating observations and progress summaries as the work is being done LIVE by the user. You are NOT the one doing the work - you are ONLY observing and recording what is being built, fixed, deployed, or configured in the other session.

SPATIAL AWARENESS: Tool executions include the working directory (tool_cwd) to help you understand:
- Which repository/project is being worked on
- Where files are located relative to the project root
- How to match requested paths to actual execution paths

WHAT TO RECORD
--------------
Focus on durable technical signal:
- What the system NOW DOES differently (new capabilities)
- What shipped to users/production (features, fixes, configs, docs)
- Changes in technical domains (auth, data, UI, infra, DevOps, d

[user] [Your previous response had no visible output. Please continue and produce a user-visible response.]

[assistant] <observation>
  <type>discovery</type>
  <title>Project Context: Projet 13 – Frank Millionaire</title>
  <subtitle>User identified active work session as belonging to "projet 13 frank millionaire".</subtitle>
  <facts>
    <fact>The active project is named "projet 13 frank millionaire" (French context).</fact>
    <fact>User established project scope on 2026-07-18 via session context message.</fact>
  </facts>
  <narrative>The user indicated that the current work session is associated with "projet 13 frank millionaire." No technical operations or file changes were observed yet — this is a project-scoping declaration establishing context for subsequent work in this session.</narrative>
  <concepts>
    <concept>why-it-exists</concept>
  </concepts>
  <files_read></files_read>
  <files_modified></files_modified>
</observation>

[user] <observed_from_primary_session>
  <what_happened>Bash</what_happened>
  <occurred_at>2026-07-18T08:47:46.731Z</occurred_at>
  <working_directory>/home/rempc/jarvis/eval-skills</working_directory>
  <parameters>"{\"command\":\"docker exec jarvis-postgres psql -U jarvis -d jarvis_main -tA -c \\\"SELECT content FROM memory_atoms WHERE id='atom_INDEX_franck_millionaire' LIMIT 1;\\\"\",\"description\":\"Read Franck Millionaire index atom\"}"</parameters>
  <outcome>"{\"stdout\":\"INDEX FRANCK MILLIONAIRE (projets #13, id STABLE point entree unique, MAJ 2026-07-18). Couple Remi + Franck Delmas.\\n\\n=== CONTEXTE ===\\nCollab Remi + Franck Delmas (French4Dev ; franckdelmas00@gmail.com ; GitHub Turbo31150 ; machine /home/turbo ; celui qui a booste JARVIS le 24/06 = MODE AUDIT + JARVIS FLOW + hooks). PRODUIT: appliance IA 100% locale 'Assistant Prive' (air-gap, RGPD/AI Act) pour cabinets juridique/compta/sante + PME — RAG docs confidentiels + transcription Voxtral + generation fichiers ; stack Mistral+Voxtral+Piper+RAG, moteur=JARVIS. ROLES (valides Remi): Franck = mains dans le moteur (build/tech), Remi = pilote business/GTM/closing + apporte vrai banc qualite + preuves JARVIS. Board convergent: goulot = POC->recurrent (Justin Welsh). AMBITION = 1M EUR. Prospect en cours: J-C Meilland (assistant-prive.fr).\\n\\n=== 2 AUDITS RENDUS A FRANCK (fichiers + mails threads) ===\\nAUDIT#1 kit commercial (repo JARVIS-Presentation-Entreprise): ~/audit-franck-assistant-prive-20260717.md. Verdict

[assistant] <observation>
  <type>discovery</type>
  <title>Projet 13 – Franck Millionaire: Full Index State Retrieved</title>
  <subtitle>Memory atom atom_INDEX_franck_millionaire read; contains full project state as of 2026-07-18.</subtitle>
  <facts>
    <fact>Collaboration: Remi (business/GTM/quality bench) + Franck Delmas (franckdelmas00@gmail.com, GitHub Turbo31150) building "Assistant Privé" — 100% local AI appliance (air-gap, RGPD/AI Act) for legal/accounting/health cabinets and SMEs.</fact>
    <fact>Product stack: Mistral + Voxtral + Piper + RAG, powered by JARVIS engine; ambition = 1M EUR revenue.</fact>
    <fact>Active prospect: J-C Meilland (assistant-prive.fr).</fact>
    <fact>Two audits delivered to Franck by email (remten341 → franckdelmas00@gmail.com); both awaiting reply (TRACK A blocked).</fact>
    <fact>AUDIT#1 verdict on commercial kit (JARVIS-Presentation-Entreprise): base saine, differentiator weak; QA-bench is tautological (refuse_invent always true if RAG, cite = bracket presence) — measures nothing.</fact>
    <fact>AUDIT#2 finding verified at source: "1435 agents" claim is inflated — true agent count ~90-100; category "Legions 10x60=600" was invented (real legions total = 25); 579 scripts/85 skills/18 CLIs were counted as agents.</fact>
    <fact>Defensible headline proposed: "~95 agents + ~800 orchestrated components, 4413 calls 99.6%, 100% local".</fact>
    <fact>Source file for agent count audit: ~/bibliotheque-prompts-multi-ia/prompts/cluster/inventaire

[user] <observed_from_primary_session>
  <what_happened>Bash</what_happened>
  <occurred_at>2026-07-18T08:48:48.533Z</occurred_at>
  <working_directory>/home/rempc/jarvis/eval-skills</working_directory>
  <parameters>"{\"command\":\"docker exec jarvis-postgres psql -U jarvis -d jarvis_main -tA -c \\\"\\nSELECT memory_atom_upsert(\\n  p_id => 'atom_franck_millionaire_aiact_factcheck_20260718',\\n  p_scope => 'franck_millionaire',\\n  p_type => 'reference',\\n  p_content => 'AI ACT — FAITS VÉRIFIÉS (projet #13 Franck Millionaire, asset GTM Assistant Privé, 2026-07-18). Source: fact-check web sources 2026 (Commission ai-act-service-desk, digital-strategy.ec.europa, Gibson Dunn Omnibus, noze, Euronews, artificialintelligenceact.eu) d une recherche Perplexity de Rémi. But: le produit se vend RGPD+AI Act compliant → le pitch DOIT reposer sur ces faits, pas sur l approximation Perplexity (qui mettait un fait FAUX au centre, cf claim#4). === VÉRITÉS === (1) AI Act = Règlement UE 2024/1689, en vigueur 01/08/2024, 1er cadre mondial, approche par risque = VRAI. (2) Risque inacceptable interdit depuis 02/02/2025 (manip cognitive, biométrie masse, notation sociale, biométrie temps réel) + AI literacy Art.4 = VRAI. (3) Digital Omnibus: accord politique 07/05/2026, ADOPTÉ Conseil 29/06/2026 → 2 nouvelles interdictions Art.5 effectives 02/12/2026 (deepfakes sexuels non-consentis + CSAM), sanctions jusqu à 35M EUR/7% CA = VRAI. (4) ERREUR PERPLEXITY à ne PAS répéter: le MÊME Omnibus REPORTE le haut-

[assistant] <observation>
  <type>feature</type>
  <title>Verified AI Act Facts Persisted as GTM Asset for Assistant Privé Pitch</title>
  <subtitle>New memory atom stores fact-checked EU AI Act regulatory timeline, correcting a key Perplexity error on high-risk deadline.</subtitle>
  <facts>
    <fact>Atom inserted: atom_franck_millionaire_aiact_factcheck_20260718, scope=franck_millionaire, type=reference, priority=7, parent=atom_INDEX_franck_millionaire.</fact>
    <fact>Sources: Commission ai-act-service-desk, digital-strategy.ec.europa, Gibson Dunn Omnibus, noze, Euronews, artificialintelligenceact.eu — all 2026 web sources via Remi's Perplexity research then fact-checked.</fact>
    <fact>CONFIRMED TRUE: AI Act = Règlement UE 2024/1689, in force 01/08/2024; unacceptable-risk prohibitions since 02/02/2025; Digital Omnibus adopted by Council 29/06/2026.</fact>
    <fact>PERPLEXITY ERROR (do not repeat): Omnibus DELAYS high-risk Annex III obligations (CE marking, EU base, risk mgmt, human-in-the-loop) from 02/08/2026 → 02/12/2027 (embedded AI → 02/08/2028) — Perplexity presented the original deadline as still active.</fact>
    <fact>3 real pitch deadlines: 02/08/2026 (Art.50 transparency — ONLY imminent, applies to their RAG/chatbot); 02/12/2026 (deepfake/CSAM bans, low B2B relevance); 02/12/2027 (heavy Annex III high-risk obligations).</fact>
    <fact>Product mapping: RAG docs/transcription/generation = LIMITED RISK — only Art.50 applies, NOT high-risk unless used for recruitment/cr

[user] --- MODE SWITCH: PROGRESS SUMMARY ---
⚠️ CRITICAL TAG REQUIREMENT — READ CAREFULLY:
• You MUST wrap your ENTIRE response in <summary>...</summary> tags.
• Do NOT use <observation> tags. <observation> output will be DISCARDED and cause a system error.
• The ONLY accepted root tag is <summary>. Any other root tag is a protocol violation.

PROGRESS SUMMARY CHECKPOINT
===========================
Write progress notes of what was done, what was learned, and what's next. This is a checkpoint to capture progress so far. The session is ongoing - you may receive more requests and tool executions after this summary. Write "next_steps" as the current trajectory of work (what's actively being worked on or coming up next), not as post-session future work. Always write at least a minimal summary explaining current progress, even if work is still in early stages, so that users see a summary output tied to each request.

Claude's Full Response to User:
Persisté : `atom_franck_millionaire_aiact_factcheck_20260718` (priority 7, rattaché à l'index projet #13).

Donc en résumé pour le projet : la recherche Perplexity était juste à 4/5, mais le claim faux (#4) est précisément celui qui aurait plombé le pitch « AI Act compliant » au premier contrôle d'un DPO/juriste chez un prospect — exactement le pattern des 2 ratés de Franck. C'est maintenant corrigé et sourcé en mémoire.

Prochaine étape logique (je ne la lance pas sans ton go) : transformer ces faits en **one-pager compliance Assistant Privé**

[assistant] <summary>
  <request>Projet 13 Franck Millionaire — index read, AI Act fact-check, GTM asset creation</request>
  <investigated>Full project index atom (atom_INDEX_franck_millionaire) was read from jarvis_main PostgreSQL, covering all context: collaboration roles, product definition, two completed audits, RAG eval harness status, and planned JARVIS improvements. A Perplexity-sourced AI Act regulatory summary was cross-checked against primary EU sources (Commission, digital-strategy.ec.europa, Gibson Dunn Omnibus, etc.).</investigated>
  <learned>
    - Perplexity's AI Act summary was 4/5 accurate but contained one critical error: it presented the high-risk Annex III deadline as 02/08/2026, when the Digital Omnibus (Council-adopted 29/06/2026) actually postpones it to 02/12/2027. Repeating this in a pitch to a legally-informed prospect (DPO, lawyer) would immediately destroy credibility.
    - The only truly imminent deadline for Assistant Privé is 02/08/2026 — Art.50 transparency obligations (AI must identify itself + label synthetic content), which directly applies to their RAG/chatbot.
    - RAG docs/transcription/generation = LIMITED RISK category, not high-risk — high-risk only triggers if used for recruitment, credit scoring, or judicial decisions.
    - Air-gap/local architecture = strong "compliance-by-design" angle: zero data exits (real RGPD) + natively delivers the human control/logs/governance Annex III will require in 2027.
    - Both of Franck's audit failures (t

[user] <observed_from_primary_session>
  <what_happened>Bash</what_happened>
  <occurred_at>2026-07-18T08:50:27.165Z</occurred_at>
  <working_directory>/home/rempc/jarvis/eval-skills</working_directory>
  <parameters>"{\"command\":\"python3 ~/jarvis/scripts/board/ask-board.py --list-domains 2>&1 | head -40\",\"description\":\"List board domains\"}"</parameters>
  <outcome>"{\"stdout\":\"- ai-engineering-applied  [6 experts, 1700 sources, 8334 chunks]\\n    AI Engineering — Applied (phases 10-19)\\n    experts: rohit-ghumare\\n- ai-engineering-fundamentals  [1 experts, 193 sources, 2579 chunks]\\n    AI Engineering — Fundamentals (phases 00-09)\\n    experts: rohit-ghumare-fundamentals\\n- behavioral-finance  [5 experts, 15 sources, 518 chunks]\\n    Behavioral Finance — Top 1%\\n    experts: kahneman, thaler, ariely, brehm, witte\\n- droit-social-fr  [1 experts, 26 sources, 223 chunks]\\n    Droit social FR — inaptitude, salarié protégé, licenciement\\n    experts: praticien-droit-social-fr\\n- ecommerce-digital  [8 experts, 85 sources, 1022 chunks]\\n    Top 1% — E-commerce Digital (produits info)\\n    experts: justin-welsh, pat-flynn, ramit-sethi, sahil-lavingia, russell-brunson, stan-leloup, tugan-bara, antoine-bm\\n- expat-malaga-admin  [1 experts, 7 sources, 117 chunks]\\n    Expatriation Malaga — Admin officielle\\n    experts: admin-officielle-es-fr\\n- funnel-info-produit-fr  [6 experts, 132 sources, 2556 chunks]\\n    Funnel info-produit FR — 9 experts Top 1%\\n    experts

[assistant] <observation>
  <type>discovery</type>
  <title>JARVIS Board Domain Inventory: 14+ Domains Listed via ask-board.py</title>
  <subtitle>Board RAG system contains 14+ expert domains with varying source/chunk counts, queried from eval-skills working directory.</subtitle>
  <facts>
    <fact>Command: python3 ~/jarvis/scripts/board/ask-board.py --list-domains; run from /home/rempc/jarvis/eval-skills.</fact>
    <fact>Largest domain by chunks: ai-engineering-applied — 6 experts, 1700 sources, 8334 chunks (phases 10-19, expert: rohit-ghumare).</fact>
    <fact>Second largest by chunks: funnel-info-produit-fr — 6 experts, 132 sources, 2556 chunks (experts: stan-leloup, antoine-bm, andre-chaperon, yann-darwin, russell-brunson, frank-kern, donald-miller, eugene-schwartz, joanna-wiebe).</fact>
    <fact>Domain relevant to Projet 13 GTM: ecommerce-digital — 8 experts, 85 sources, 1022 chunks (includes justin-welsh, pat-flynn, ramit-sethi, hormozi-adjacent experts).</fact>
    <fact>Domain relevant to AI Act pitch: prompt-engineering-anthropic — 1 expert, 13 sources, 315 chunks (partially visible, cut off).</fact>
    <fact>Smallest domains: liberty-webi-jody-cavalie (2 experts, 8 sources, 48 chunks) and expat-malaga-admin (1 expert, 7 sources, 117 chunks).</fact>
    <fact>Behavioral finance domain available: kahneman, thaler, ariely, brehm, witte — 5 experts, 15 sources, 518 chunks.</fact>
    <fact>French legal domain present: droit-social-fr (inaptitude, salarié protégé, licenciement)

[user] <observed_from_primary_session>
  <what_happened>Write</what_happened>
  <occurred_at>2026-07-18T08:51:28.470Z</occurred_at>
  <working_directory>/home/rempc/jarvis/eval-skills</working_directory>
  <parameters>"{\"file_path\":\"/home/rempc/franck-assistant-prive-aiact-onepager-20260718.md\",\"content\":\"# Assistant Privé — La conformité AI Act comme argument de vente\\n\\n> **One-pager GTM — projet #13 Franck Millionaire · v1 · 18/07/2026**\\n> Faits vérifiés le 18/07/2026 contre sources primaires UE (voir bas de page). À tenir tels quels : chaque chiffre est défendable devant un DPO ou un juriste. Règle du projet : petit fait solide > gros argument qui s'effondre au contrôle.\\n\\n---\\n\\n## Le contexte que le prospect a en tête (dans 15 jours)\\n\\nLe **2 août 2026**, la vague la plus lourde de l'**AI Act** (Règlement UE 2024/1689) entre en application. Les cabinets juridiques, comptables et de santé le savent — mais **90 % d'entre eux surestiment ce qui les frappe réellement à cette date**, parce que la presse a mélangé le calendrier initial et les reports votés depuis.\\n\\nC'est exactement là que se joue l'argument Assistant Privé : **on vend la clarté + la conformité by-design.**\\n\\n---\\n\\n## Les 3 échéances réelles (post-Digital Omnibus)\\n\\n| Date | Ce qui s'applique | Qui est concerné |\\n|---|---|---|\\n| **02/08/2026** *(dans ~15 j)* | **Article 50 — Transparence** : tout système IA interagissant avec des humains doit **se signaler comme IA** + labelliser l

[assistant] <observation>
  <type>feature</type>
  <title>AI Act GTM One-Pager Created for Assistant Privé (v1)</title>
  <subtitle>Sales-ready compliance document written with verified EU AI Act facts, anti-oversell rules, and compliance-by-design positioning.</subtitle>
  <facts>
    <fact>File created: /home/rempc/franck-assistant-prive-aiact-onepager-20260718.md (v1, 18/07/2026).</fact>
    <fact>Document opens by framing the prospect's confusion: 90% of target cabinets overestimate what hits them on 02/08/2026 due to press conflating original and revised timelines.</fact>
    <fact>Core sales table presents 3 real post-Digital Omnibus deadlines: 02/08/2026 (Art.50 transparency — all AI systems), 02/12/2026 (deepfake/CSAM bans — low B2B relevance), 02/12/2027 (Annex III high-risk — delayed from 02/08/2026).</fact>
    <fact>Honest legal caveat included: Omnibus delay only fully binding upon JO publication; Council adopted 29/06/2026 → publication imminent; recommends preparing as if 02/08/2026 deadline stands until JO appears.</fact>
    <fact>Anti-oversell rule codified in document: never tell a cabinet they are high-risk — incorrect for standard RAG/transcription use and backfires with the first lawyer at the prospect.</fact>
    <fact>Closing positioning line: "Un cabinet ne peut pas mettre le secret de ses clients dans un chatbot cloud. Assistant Privé met l'IA là où la donnée doit rester : chez vous. Conforme RGPD aujourd'hui, prêt pour l'AI Act haut-risque de 2027 — sans rien c

[user] <observed_from_primary_session>
  <what_happened>Bash</what_happened>
  <occurred_at>2026-07-18T08:51:51.827Z</occurred_at>
  <working_directory>/home/rempc/jarvis/eval-skills</working_directory>
  <parameters>"{\"command\":\"docker exec jarvis-postgres psql -U jarvis -d jarvis_main -tA -c \\\"\\nSELECT memory_atom_upsert(\\n  p_id => 'atom_franck_millionaire_aiact_onepager_20260718',\\n  p_scope => 'franck_millionaire',\\n  p_type => 'deliverable',\\n  p_content => 'ONE-PAGER GTM CRÉÉ (projet #13, 2026-07-18) — ~/franck-assistant-prive-aiact-onepager-20260718.md. Asset commercial: la conformité AI Act comme argument de vente Assistant Privé. Ancré STRICTEMENT sur atom_franck_millionaire_aiact_factcheck_20260718 (faits vérifiés web, 0 claim fabriqué — rédigé Opus, PAS délégué gemma pour éviter re-hallucination juridique). Contenu: 3 deadlines réelles (02/08/2026 Art.50 transparence = seule imminente + sandboxes ; 02/12/2026 interdictions deepfakes/CSAM ; 02/12/2027 haut-risque Annexe III reporté par Omnibus). Angle de fermeture = compliance-by-design par air-gap/local (RGPD aujourd hui + AI Act 2027-ready: contrôle humain/logs/gouvernance natifs). GARDE-FOU ANTI-SURVENTE explicite: RAG/transcription = risque limité, PAS haut-risque → ne jamais dire au cabinet vous êtes high-risk (faux + se retourne au 1er juriste). Board NON consulté: aucun domaine ne couvre GTM B2B compliance (plus proches = ecommerce-digital/funnel B2C), + verdict board déjà en index (goulot POC->récurrent)

[assistant] <observation>
  <type>decision</type>
  <title>One-Pager Logged as Deliverable Atom; Opus Used Over gemma to Avoid Legal Re-Hallucination</title>
  <subtitle>Atom atom_franck_millionaire_aiact_onepager_20260718 inserted; documents rationale for model choice and why board was not consulted.</subtitle>
  <facts>
    <fact>Atom inserted: atom_franck_millionaire_aiact_onepager_20260718, type=deliverable, priority=6, parents=[atom_franck_millionaire_aiact_factcheck_20260718, atom_INDEX_franck_millionaire].</fact>
    <fact>Model choice documented: one-pager written by Opus, NOT delegated to gemma — explicit rationale: risk of legal re-hallucination on regulatory content.</fact>
    <fact>Board explicitly NOT consulted: no domain covers GTM B2B compliance; closest domains (ecommerce-digital, funnel-info-produit-fr) are B2C-oriented; board verdict on goulot (POC→recurring per Justin Welsh) already in index.</fact>
    <fact>Next possible steps logged in atom: adapt as email to Franck OR prospect-facing version for J-C Meilland (assistant-prive.fr).</fact>
  </facts>
  <narrative>After creating the one-pager file, the primary session immediately logged a deliverable-type memory atom to track it. The atom captures two important meta-decisions: (1) using Opus directly instead of a lighter model (gemma) for legal/regulatory content to avoid introducing new hallucinations into verified facts, and (2) skipping the board consultation because no available domain maps to B2B compliance GTM —

[user] --- MODE SWITCH: PROGRESS SUMMARY ---
⚠️ CRITICAL TAG REQUIREMENT — READ CAREFULLY:
• You MUST wrap your ENTIRE response in <summary>...</summary> tags.
• Do NOT use <observation> tags. <observation> output will be DISCARDED and cause a system error.
• The ONLY accepted root tag is <summary>. Any other root tag is a protocol violation.

PROGRESS SUMMARY CHECKPOINT
===========================
Write progress notes of what was done, what was learned, and what's next. This is a checkpoint to capture progress so far. The session is ongoing - you may receive more requests and tool executions after this summary. Write "next_steps" as the current trajectory of work (what's actively being worked on or coming up next), not as post-session future work. Always write at least a minimal summary explaining current progress, even if work is still in early stages, so that users see a summary output tied to each request.

Claude's Full Response to User:
One-pager monté et logué.

📄 **`~/franck-assistant-prive-aiact-onepager-20260718.md`**

Ce qu'il contient :
- **Le hook** : dans 15 jours (02/08/2026), les cabinets savent que « ça arrive » mais surestiment ce qui les frappe → Assistant Privé vend la **clarté + la conformité by-design**.
- **Les 3 deadlines réelles** en tableau (02/08 transparence · 02/12/2026 deepfakes · 02/12/2027 haut-risque reporté), avec le caveat « JO pas encore publié » assumé.
- **Ce qui touche vraiment un cabinet** : RAG/transcription = risque limité → seul l'Art. 50 m

[assistant] <summary>
  <request>Projet 13 Franck Millionaire — AI Act one-pager GTM créé, vérifié et logué en mémoire JARVIS</request>
  <investigated>Board domains listed via ask-board.py to assess whether any domain could contribute to GTM B2B compliance content. Conclusion: no domain covers this angle directly (ecommerce-digital and funnel-info-produit-fr are B2C-oriented); board consultation skipped as low value-to-cost ratio for this task.</investigated>
  <learned>
    - Writing legally-sensitive regulatory content must NOT be delegated to lighter models (gemma): risk of re-introducing hallucinations into facts that were just corrected from Perplexity. Opus used directly for the one-pager.
    - The board's strategic verdict on the project (bottleneck = POC→recurring, Justin Welsh framework) is already in the index atom — no need to re-query it.
    - Anti-oversell discipline must be explicitly codified in sales documents, not left implicit: for cabinet use cases, RAG/transcription = limited risk, NOT high-risk. Saying "vous êtes high-risk" is factually wrong and backfires with the first lawyer at the prospect.
  </learned>
  <completed>
    - GTM one-pager written and saved: ~/franck-assistant-prive-aiact-onepager-20260718.md (v1, 18/07/2026).
    - Document covers: 3 real post-Digital Omnibus deadlines (02/08/2026 Art.50 transparency, 02/12/2026 deepfakes/CSAM, 02/12/2027 Annex III high-risk delayed), product risk mapping, compliance-by-design air-gap closing angle, and explicit