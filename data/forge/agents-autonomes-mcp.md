# Agents Autonomes & MCP

> Référence `agents-autonomes-mcp` · 99 €

## Plan

## Module 1 – Fondamentaux des agents autonomes  
**Objectif mesurable** : Être capable de décrire l’architecture d’un agent autonome et d’implémenter un boucle perception‑action basique en Python.  
- Notion 1 : Définition formelle d’un agent (fonction d’état, fonction d’action, modèle d’environnement).  
- Notion 2 : Cycle perception‑déduction‑action (P‑D‑A) et ses variantes (P‑P‑A, P‑R‑A).  
- Notion 3 : Modélisation de l’environnement : MDP (Markov Decision Process) et POMDP (Partially Observable MDP).  
- Notion 4 : Gestion du temps réel et contraintes de latence dans la boucle d’interaction.  

## Module 2 – Modélisation et simulation d’environnements  
**Objectif mesurable** : Concevoir un simulateur d’environnement compatible OpenAI Gym et y intégrer des dynamiques non stationnaires.  
- Notion 1 : Interfaces Gym (Env, Step, Reset, Render) et création d’environnements personnalisés.  
- Notion 2 : Implémentation de dynamiques stochastiques (bruit, transitions probabilistes).  
- Notion 3 : Paramétrisation de scénarios (variabilité des objectifs, contraintes de ressources).  
- Notion 4 : Validation de la cohérence de l’environnement via tests unitaires et propriétés de Markov.  

## Module 3 – Méthodologie MCP (Model‑Condition‑Policy)  
**Objectif mesurable** : Appliquer la chaîne Model‑Condition‑Policy pour générer, tester et itérer une politique de décision dans un environnement donné.  
- Notion 1 : Construction du **Model** – représentation du monde (graphes de connaissances, modèles probabilistes).  
- Notion 2 : Définition du **Condition** – critères d’activation (seuils, triggers, événements).  
- Notion 3 : Formulation de la **Policy** – mapping condition → action (règles, réseaux de neurones, arbres de décision).  
- Notion 4 : Boucle d’optimisation MCP (re‑fit du modèle, recalibration des conditions, mise à jour de la policy).  

## Module 4 – Implémentation avec les frameworks d’agents (LangChain, Auto‑GPT, CrewAI)  
**Objectif mesurable** : Déployer un agent autonome complet en utilisant au moins deux des frameworks cités et le faire fonctionner en mode « zero‑shot ».  
- Notion 1 :

---

## Module 1 — contenu

## Module 1 – Fondamentaux des agents autonomes  

### 1.1 Définition formelle d’un agent  

| Élément | Notation | Description |
|--------|----------|-------------|
| **État interne** | \(s_t \in \mathcal{S}\) | Variable(s) maintenues par l’agent (ex. historique d’observations, paramètres de modèle). |
| **Perception** | \(o_t = \mathcal{O}(e_t)\) | Fonction d’observation qui transforme la configuration de l’environnement \(e_t\) en une observation exploitable. |
| **Fonction d’état** | \(\phi: \mathcal{S}\times\mathcal{O}\rightarrow\mathcal{S}\) | Met à jour l’état interne à chaque pas de temps : \(s_{t+1}= \phi(s_t,o_t)\). |
| **Fonction d’action** | \(\pi: \mathcal{S}\rightarrow\mathcal{A}\) | Politique déterministe ou stochastique qui génère une action à partir de l’état interne. |
| **Modèle d’environnement** | \(T(e_t,a_t)=e_{t+1}\) | Transition (déterministe ou probabiliste) qui décrit comment l’action modifie l’environnement. |

Un **agent autonome** est donc le tuple \((\phi,\pi,\mathcal{O})\) couplé à un modèle d’environnement \(T\).  

> **Vérifiable** : La définition ci‑dessus correspond à la formulation de Russell & Norvig (2020) et aux travaux de Sutton & Barto (2018) sur les processus décisionnels.

---

### 1.2 Cycle perception‑déduction‑action (P‑D‑A)  

| Variante | Schéma | Usage typique |
|----------|--------|---------------|
| **P‑D‑A** | \(o_t \rightarrow s_{t+1} = \phi(s_t,o_t) \rightarrow a_t = \pi(s_{t+1})\) | Agents avec modèle interne (ex. robot mobile). |
| **P‑P‑A** | \(o_t \rightarrow p_t = \psi(o_t) \rightarrow a_t = \pi(p_t)\) | Systèmes réactifs où la déduction se limite à un pré‑traitement (ex. filtres de bruit). |
| **P‑R‑A** | \(o_t \rightarrow r_t = \rho(o_t) \rightarrow a_t = \pi(r_t)\) | Agents qui utilisent une fonction de récompense immédiate (ex. bandits). |

**Déduction** peut être :  
* **Logique** (ex. règles Horn).  
* **Probabiliste** (ex. inférence Bayésienne).  
* **Apprentissage** (ex. réseau de neurones).  

---

### 1.3 Modélisation de l’environnement  

#### 1.3.1 MDP (Markov Decision Process)  

Un MDP est le quintuple \((\mathcal{S},\mathcal{A},P,R,\gamma)\) où :

* \(P(s'|s,a)\) = probabilité de transition.  
* \(R(s,a,s')\) = récompense instantanée.  
* \(\gamma\in[0,1]\) = facteur d’actualisation.

**Propriété de Markov** : \(P(s_{t+1}|s_t,a_t)=P(s_{t+1}|s_{0:t},a_{0:t})\).  

#### 1.3.2 POMDP (Partially Observable MDP)  

Un POMDP ajoute une fonction d’observation \(O(o|s,a)\) et un **belief state** \(b_t(s)=P(s_t=s|h_t)\) où \(h_t\) est l’historique des observations et actions.  

> **Vérifiable** : La différence entre MDP et POMDP est décrite dans Kaelbling, Littman & Cassandra (1998).

---

### 1.4 Gestion du temps réel et contraintes de latence  

| Concept | Description | Implémentation concrète |
|---------|-------------|------------------------|
| **Cycle d’horloge** | Durée fixe \(\Delta t\) entre deux itérations du boucle P‑D‑A. | `while True: start = time.time(); … ; time.sleep(max(0, Δt - (time.time()-start)))` |
| **Deadline** | L’action doit être disponible avant \(t_{deadline}=t_{now}+d\). | Lever une exception si `time.time()>deadline`. |
| **Priorisation** | Certaines perceptions (ex. capteurs de sécurité) sont traitées en priorité. | Utiliser une file de priorité (`heapq`). |
| **Jitter** | Variation de la durée réelle du cycle. | Mesurer `Δactual = time.time()-last_start`; logguer si `|Δactual-Δt| > ε`. |

**Pièges fréquents**  
1. **Blocage I/O** : appel bloquant (ex. `socket.recv()`) prolonge le cycle. Solution : socket non bloquant ou `select`.  
2. **Garbage collection** : en Python, le GC peut introduire des pauses imprévisibles. Utiliser `gc.disable()` pendant les phases critiques ou pré‑allouer les objets.  
3. **Overflow de la file d’attente** : si la production de perceptions dépasse la consommation, la latence augmente. Implémenter un mécanisme de **dropping** ou de **back‑pressure**.  

---

## Exemple de code : boucle perception‑déduction‑action basique  

```python
# -*- coding: utf-8 -*-
"""
Agent autonome minimaliste illustrant le cycle P‑D‑A.
Environnement : ligne 1‑D où l'agent doit atteindre la position 10.
"""

import time
import random
from collections import deque

# ---------- Paramètres ----------
TARGET_POS = 10          # objectif
MAX_SPEED   = 2           # vitesse maximale (cases /

---

## Module 2 — contenu

## Module 2 – Modélisation et simulation d’environnements  

### 2.1 Interfaces Gym : structure minimale d’un environnement  

| Méthode | Signature | Rôle | Retour attendu |
|--------|-----------|------|-----------------|
| `__init__(self, **kwargs)` | `self` | Initialise les variables d’état, les espaces d’observation et d’action. | – |
| `reset(self, seed=None, options=None)` | `self, seed: int | None = None, options: dict | None = None` | (re)définit l’état interne, fixe le générateur aléatoire. | `obs, info` où `obs` appartient à `observation_space`. |
| `step(self, action)` | `self, action` | Applique `action`, calcule la transition, la récompense, le drapeau `done` et les informations auxiliaires. | `obs, reward, terminated, truncated, info`. |
| `render(self, mode='human')` | `self, mode='human'` | Visualise l’état actuel. | `None` (mode *human*) ou tableau d’image (mode *rgb_array*). |
| `close(self)` | `self` | Libère les ressources (fenêtres, fichiers). | – |

*Contraintes* :  
- `observation_space` et `action_space` doivent être des instances de `gym.spaces.*`.  
- `reset` doit renvoyer **un tuple** `(obs, info)` depuis Gym v0.26+.  
- `step` doit renvoyer **cinq** valeurs depuis Gym v0.26+.  

### 2.2 Implémentation d’un environnement stochastique non‑stationnaire  

#### 2.2.1 Description du problème  

Un robot se déplace sur une grille 5 × 5.  
- L’état est la position `(x, y)`.  
- L’action est un déplacement parmi `{0:up, 1:right, 2:down, 3:left}`.  
- La dynamique change toutes les `T_change = 20` étapes : la probabilité de glissement (`p_slip`) augmente linéairement de 0 % à 30 %.  
- La récompense est `+1` lorsqu’on atteint la case cible `(4,4)`, sinon `0`.  

#### 2.2.2 Code complet (commenté)  

```python
# -*- coding: utf-8 -*-
import gym
from gym import spaces
import numpy as np

class GridWorldNonStationary(gym.Env):
    """
    Environnement 5x5 avec dynamique de glissement qui évolue
    toutes les 20 étapes (non‑stationnaire).
    """
    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(self, grid_size: int = 5, T_change: int = 20, max_steps: int = 200):
        super().__init__()
        self.grid_size = grid_size
        self.T_change = T_change
        self.max_steps = max_steps

        # Espace d'observation : position (x, y) codée en entier
        self.observation_space = spaces.Discrete(grid_size * grid_size)
        # Espace d'action : 4 déplacements cardinales
        self.action_space = spaces.Discrete(4)

        self._state = None               # position (x, y)
        self._step_counter = 0
        self._p_slip = 0.0                # probabilité de glissement actuelle
        self._rng = np.random.default_rng()  # RNG indépendant du seed Gym

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Position de départ fixe pour la reproductibilité des tests
        self._state = (0, 0)
        self._step_counter = 0
        self._p_slip = 0.0
        # Retourner l'index de l'état (flattened)
        obs = self._pos_to_index(self._state)
        return obs, {}

    # ------------------------------------------------------------------
    # Méthodes utilitaires
    # ------------------------------------------------------------------
    def _pos_to_index(self, pos):
        """Convertit (x, y) → indice unique."""
        x, y = pos
        return y * self.grid_size + x

    def _index_to_pos(self, idx):
        """Convertit indice → (x, y)."""
        y, x = divmod(idx, self.grid_size)
        return (x, y)

    def _apply_slip(self, action):
        """Avec probabilité p_slip, renvoie une action aléatoire."""
        if self._rng.random() < self._p_slip:
            return self._rng.integers(0, self.action_space.n)
        return action

    def _move(self, pos, action):
        """Déplace la position selon l’action (sans sortir de la grille)."""
        x, y = pos
        if action == 0:   # up
            y = max(y - 1, 0)
        elif action == 1: # right
            x = min(x + 1, self.grid_size - 1)
        elif action == 2: # down
            y = min(y + 1, self.grid_size - 1)
        elif action == 3: # left
            x = max(x - 1, 0)
        return (x, y)

    # ------------------------------------------------------------------
    # Boucle principale
    # ------------------------------------------------------------------
    def step(self, action):
        assert self.action_space.contains(action), f"Action {action} invalide"

        # 1️⃣ Mise à jour du glissement (non‑stationnaire)
        if self._step_counter % self.T_change == 0 and self._step_counter > 0:
            # Augmente linéairement

---

## Module 3 — contenu

## Module 3 – Méthodologie MCP (Model‑Condition‑Policy)

### 1. Construction du **Model**  

| Concept | Définition précise | Implémentation typique |
|--------|--------------------|-----------------------|
| **Modèle de monde** | Représentation explicite des variables d’état, de leurs dépendances probabilistes et/ou structurelles. | *Graphes de connaissances* (RDF/OWL) ou *modèles probabilistes* (Bayesian Networks, Factor Graphs). |
| **État factuel** | Tuple `s = (s₁,…,s_n)` où chaque `s_i` est une variable aléatoire ou déterministe décrivant l’environnement à un instant `t`. | En Python : `state = {"position": (x, y), "battery": 0.73, "task": "delivery"}`. |
| **Fonction de transition** | `T(s'|s,a)` = probabilité de passer à l’état `s'` après l’action `a`. | Implémentée comme une table de probabilité ou un réseau de neurones `transition_model(s, a) → distribution`. |
| **Fonction d’observation** (POMDP) | `O(o|s,a)` = probabilité d’observer `o` dans l’état `s` après l’action `a`. | Utilisée uniquement si l’agent ne voit pas l’état complet. |

#### Exemple : Modèle Bayésien d’un robot mobile

```python
import numpy as np
import networkx as nx
import pgmpy.models
import pgmpy.inference

# Variables : Position (grid), Battery (float), Obstacle (bool)
model = pgmpy.models.BayesianModel(
    [("Battery", "Position"),   # batterie influence la capacité à se déplacer
     ("Obstacle", "Position")]  # présence d’obstacle conditionne la position
)

# Définition des tables de probabilité (CPT)
cpt_battery = np.array([[0.9, 0.1]])                     # 90 % chargé, 10 % faible
cpt_obstacle = np.array([[0.8, 0.2]])                    # 80 % pas d’obstacle, 20 % obstacle
cpt_position = np.array([
    # Battery, Obstacle -> Position (4 cells)
    [0.7, 0.2, 0.1, 0.0],   # Battery=high, Obstacle=none
    [0.4, 0.4, 0.2, 0.0],   # Battery=high, Obstacle=present
    [0.3, 0.3, 0.3, 0.1],   # Battery=low,  Obstacle=none
    [0.1, 0.2, 0.5, 0.2]    # Battery=low,  Obstacle=present
])
model.add_cpds(
    pgmpy.factors.discrete.TabularCPD("Battery", 2, cpt_battery),
    pgmpy.factors.discrete.TabularCPD("Obstacle", 2, cpt_obstacle),
    pgmpy.factors.discrete.TabularCPD(
        "Position", 4,
        cpt_position,
        evidence=["Battery", "Obstacle"],
        evidence_card=[2, 2]
    )
)

assert model.check_model()   # vérifie la cohérence du graphe

inference = pgmpy.inference.VariableElimination(model)

def predict_position(battery_state: int, obstacle_state: int):
    """Renvoie la distribution a‑posteriori sur Position."""
    q = inference.query(
        variables=["Position"],
        evidence={"Battery": battery_state, "Obstacle": obstacle_state}
    )
    return q["Position"].values
```

*Points de vérification*  
- `model.check_model()` lève une exception si les CPT ne sont pas normalisées.  
- La fonction `predict_position` renvoie un tableau de 4 probabilités qui somme à 1 (vérifiable avec `np.isclose(np.sum(...), 1.0)`).

---

### 2. Définition du **Condition**  

| Élément | Description | Implémentation concrète |
|--------|-------------|------------------------|
| **Trigger** | Événement discret (ex. `battery < 0.2`). | `if state["battery"] < 0.2: trigger = "low_battery"` |
| **Seuil** | Valeur numérique ou probabiliste à dépasser. | `if prob_obstacle > 0.7: trigger = "avoid"` |
| **Fenêtre temporelle** | Condition qui dépend d’une séquence d’observations (ex. moyenne glissante). | `np.mean(last_5_battery) < 0.3` |
| **Priorité** | Ordre d’évaluation lorsqu’il y a plusieurs triggers actifs. | Dictionnaire `priority = {"emergency":0, "low_battery":1, "normal":2}`. |

#### Exemple : Condition de recharge

```python
def evaluate_conditions(state, history):
    """Retourne le nom de la condition la plus prioritaire."""
    # 1. Urgence : batterie critique
    if state["battery"] < 0.05:
        return "emergency_recharge"
    # 2. Recharge planifiée : batterie < 0.2 pendant plus de 3 pas consécutifs
    low_batt_seq = [s["battery"] < 0.2 for s in history[-5:]]
    if sum(low_batt_seq) >= 3:
        return "scheduled_recharge"
    # 3. Aucun déclencheur
    return "operate"
```

*Pièges*  
- **Condition non exclusive** : si deux triggers sont vrais, la priorité doit être explicitement gérée, sinon le système peut choisir arbitrairement.  
- **Oscillation** : une condition qui s’active/désactive à chaque pas crée des boucles infinies (`recharge` ↔ `operate`). Utiliser un *hysteresis* (ex. seuil haut

---

## Module 4 — contenu

## 4.1. Choix du cadre d’exécution  

| Cadre | Version pip (au 14 / 08 / 2026) | Principaux modules | Points forts | Limites notables |
|-------|-------------------------------|--------------------|--------------|------------------|
| **LangChain** | `langchain==0.2.5` | `langchain`, `langchain-community`, `langchain-openai` | Orchestration fine‑grained (chains, agents, tools), support natif du modèle de base (OpenAI, Anthropic, Ollama). | Nécessite la définition explicite des **tools** ; la gestion du contexte est manuelle. |
| **Auto‑GPT** | `autogpt==0.6.2` | `autogpt`, `openai`, `tiktoken` | Boucle de réflexion auto‑régulée (plan → exécuter → critique → ré‑plan). | Architecture monolithique, difficile à injecter des outils externes sans forker. |
| **CrewAI** | `crewai==0.3.11` | `crewai`, `crewai-tools`, `langchain-core` | Modèle de **crew** (multiple agents) avec coordination via **task manager**. | Documentation encore en évolution, moins d’exemples “zero‑shot”. |

Pour le module, nous implémenterons **un agent zero‑shot** avec **LangChain** et **CrewAI**. Auto‑GPT sera mentionné à titre comparatif.

---

## 4.2. Architecture générale de l’agent zero‑shot  

```
User Prompt ──► LLM (LLMProvider) ──► Agent (LangChain) ──► Tool Call(s) (API, DB, etc.)
                │                         │
                │                         └─► CrewAI Coordinator (optionnel)
                ▼
            Réponse finale
```

* **LLMProvider** : modèle de base (ex. `gpt-4o-mini`).  
* **Agent** : `ZeroShotAgent` de LangChain, qui crée dynamiquement des *tools* à partir du prompt.  
* **Tool** : fonction Python décorée `@tool` (ex. recherche web, lecture CSV).  
* **CrewAI Coordinator** (facultatif) : orchestre plusieurs sous‑agents (ex. *Researcher*, *Writer*).  

---

## 4.3. Implémentation avec LangChain  

### 4.3.1. Installation et configuration de base  

```bash
pip install "langchain[all]" openai
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 4.3.2. Définition de deux outils simples  

```python
# file: tools.py
from typing import List
from langchain.tools import tool

@tool
def fetch_url(url: str) -> str:
    """
    Récupère le contenu texte d’une URL.
    Retourne le HTML brut (limité à 2000 caractères pour éviter les dépassements de token).
    """
    import httpx
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    return resp.text[:2000]

@tool
def read_csv(path: str) -> List[dict]:
    """
    Lit un fichier CSV local et renvoie la liste des lignes sous forme de dict.
    Le CSV doit être encodé en UTF‑8 et contenir une ligne d’en‑tête.
    """
    import csv, pathlib
    p = pathlib.Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Fichier CSV introuvable : {path}")
    with p.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)
```

### 4.3.3. Construction de l’agent zero‑shot  

```python
# file: agent_zero_shot.py
import os
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from tools import fetch_url, read_csv

# 1️⃣ LLM – on utilise le modèle le plus économique compatible avec les outils
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.0,          # zéro‑shot = déterministe
    max_tokens=2000,
)

# 2️⃣ Enregistrement des outils dans la liste attendue par LangChain
tools = [fetch_url, read_csv]

# 3️⃣ Initialisation de l’agent.  AgentType.ZERO_SHOT_REACT_DESCRIPTION
#    crée un prompt qui décrit chaque outil et laisse le LLM choisir.
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,            # affichage du raisonnement interne
)

def run(prompt: str) -> str:
    """Exécute le prompt via l’agent zero‑shot et renvoie la réponse finale."""
    return agent.run(prompt)

if __name__ == "__main__":
    # Exemple d’usage
    user_prompt = (
        "Quel est le prix moyen du Bitcoin le 1er janvier 2024 ? "
        "Utilise le site https://www.coindesk.com/price/bitcoin et renvoie le résultat sous forme JSON."
    )
    print(run(user_prompt))
```

#### Explication du flux  

1. **LLM** reçoit le prompt complet, incluant la description des deux outils.  
2. Le **Zero‑Shot ReAct** génère une séquence d’actions du type `Action: fetch_url` puis `Action: read_csv` si nécessaire.  
3. Chaque appel d’outil est exécuté immédiatement, le résultat est injecté dans le contexte du LLM.  
4. Le LLM produit la réponse finale.  

### 4.3.4. Points de vérification (tests unit

---

## Module 5 — contenu

## Module 5 – Déploiement, scalabilité et supervision d’agents autonomes en production  

### 5.1 Architecture de déploiement (Docker + Kubernetes)  

| Niveau | Action | Détail technique vérifiable |
|--------|--------|-----------------------------|
| **Conteneurisation** | Créer un `Dockerfile` minimaliste (base `python:3.11-slim`). | `FROM python:3.11-slim` assure une image de < 120 Mo (mesurée avec `docker images`). |
| **Isolation des dépendances** | Utiliser un *virtual environment* dans le conteneur (`venv`). | `python -m venv /opt/venv && . /opt/venv/bin/activate && pip install -r requirements.txt` garantit que les paquets sont installés dans `/opt/venv`. |
| **Entrypoint** | `ENTRYPOINT ["python", "-m", "agent.main"]`. | Lancement du module `agent/main.py` au démarrage du conteneur. |
| **Orchestration** | Déployer le conteneur dans un pod Kubernetes avec `resources.limits` (CPU = 500 m, RAM = 256 Mi). | `kubectl top pod` montre la consommation réelle, qui ne doit pas dépasser les limites. |
| **Service** | Exposer le pod via un `ClusterIP` + `Service` `type: LoadBalancer` si besoin d’accès externe. | Le service crée une IP publique (`kubectl get svc`). |
| **Rolling update** | `spec.strategy.type: RollingUpdate` avec `maxUnavailable: 0`, `maxSurge: 1`. | Aucun temps d’indisponibilité pendant le déploiement (`kubectl rollout status`). |

#### Schéma d’architecture  

```
+-------------------+       +-------------------+       +-------------------+
|  Ingress (NGINX)  | <---> |  Service (L4)     | <---> |  Pod (agent)      |
+-------------------+       +-------------------+       +-------------------+
          ^                         ^                         ^
          |                         |                         |
   TLS termination            Load‑balancing            OpenTelemetry
```

---

### 5.2 Gestion de l’état persistant  

| Besoin | Outil recommandé | Raison technique |
|--------|------------------|-------------------|
| Mémoire de courte durée (caches, tokens) | **Redis** (mode *cluster*) | Latence < 1 ms en lecture/écriture (mesurée avec `redis-benchmark`). |
| Historique durable (logs, traces) | **PostgreSQL** (partitionnement par date) | Garantit ACID, supporte `JSONB` pour stocker des métriques. |
| Snapshots de modèles | **MinIO** (compatible S3) | S3‑compatible, chiffrement côté serveur (`SERVER_SIDE_ENCRYPTION`). |

#### Exemple d’accès atomique à un compteur de décisions  

```python
import redis
from typing import Literal

r = redis.StrictRedis(host="redis", port=6379, db=0)

def incr_decision_counter(agent_id: str) -> int:
    """
    Incrémente de façon atomique le compteur de décisions d'un agent.
    Retourne la valeur après incrément.
    """
    key = f"agent:{agent_id}:decision_counter"
    # Redis incr est atomic (single‑threaded server)
    return r.incr(key)

# Usage
current = incr_decision_counter("alpha")
print(f"Compteur actuel = {current}")
```

*Vérifiable* : `INCR` est décrit comme atomique dans la documentation officielle de Redis (v6.2).  

---

### 5.3 Monitoring & logging (Prometheus + Grafana + OpenTelemetry)  

1. **Instrumentation du code** – ajouter un `MeterProvider` OpenTelemetry.  
2. **Exporter les métriques** vers le endpoint `/metrics` exposé par le conteneur.  
3. **Scraping** par Prometheus (configuration `scrape_configs`).  
4. **Alerting** – règle Prometheus `alert: HighDecisionLatency`.  

#### Code d’instrumentation (Python 3.11)  

```python
# agent/monitoring.py
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider

# 1️⃣ Crée le lecteur Prometheus (expose /metrics sur 8000)
prometheus_reader = PrometheusMetricReader(port=8000)
provider = MeterProvider(metric_readers=[prometheus_reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter(__name__)

# 2️⃣ Définit des instruments
decision_latency = meter.create_histogram(
    name="agent_decision_latency_seconds",
    description="Temps (s) entre perception et action",
    unit="s",
)

# 3️⃣ Fonction utilitaire à appeler autour de la boucle décision
def record_decision_latency(duration_s: float) -> None:
    """
    Enregistre la latence d’une