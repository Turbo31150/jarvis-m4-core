[user] ## Adversarial Claim Verifier (voter 1/3)

Be SKEPTICAL. Try to REFUTE this claim. ≥2/3 refutations kill it.

## Research question
Comment les systèmes multi-agents en production pondèrent, routent et arbitrent entre agents en 2026 ? Techniques documentées : routage par score, vote pondéré, consensus, cascade de repli, sélection d'outils par embedding, bandits/apprentissage du routage. Pour chacune : preuves d'efficacité, coûts, modes de défaillance connus. Contexte : un routeur local pondère par popularité 0,3 + reproductibilité 0,5 + sûreté 0,2 pour choisir parmi 268 895 recettes réparties en 9 familles, avec 319 agents enregistrés. Question centrale : quelles pondérations et quels mécanismes d'arbitrage ont fait leurs preuves, et lesquels échouent silencieusement à l'échelle ?

## Claim under review
"Les algorithmes de bandit linéaires classiques (LinUCB 0,6166 ; LinTS 0,6430 ; ε-greedy 0,6556) sont battus de 9 à 13 points par une politique non linéaire (REINFORCE + MLP, 0,7432) sur le même contexte ; et leur exploration conservatrice biaise systématiquement vers les actions les moins chères, donc les moins performantes — mode de défaillance mesurable d'un score de routage linéaire."

**Source:** https://arxiv.org/pdf/2510.07429 (primary)
**Supporting quote:** "Notably, bandit approaches tend to yield slightly lower costs, suggesting that their conservative exploration might favor cheaper models at the expense of performance. [...] While classic bandit algorithms provide a

[assistant] Let me check the internal consistency — specifically the linear-vs-MLP head ablation.

[assistant] Let me check the reward definition and whether bandit hyperparameters were tuned.

[assistant] I have the decisive evidence directly from the primary source. Let me record the verdict.