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

> **Vérifiable** : La différence entre MDP et POMDP est décrite dans Kaelbing, Littman & Cassandra (1998).

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

Un robot se déplace sur une grille.  
- L’état est la position `(x, y)`.  
- L’action est un déplacement parmi les quatre directions cardinales.  
- La dynamique change de façon périodique : la probabilité de glissement (`p_slip`) augmente de façon linéaire au fil du temps.  
- La récompense est positive lorsqu’on atteint la case cible `(4,4)`, sinon aucune récompense.  

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
```