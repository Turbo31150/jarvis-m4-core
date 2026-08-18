# LangChain & LangGraph pour Agents

> Référence `langchain-ia` · 79 €

## Plan

## Module 1 – Fondamentaux de LangChain  

**Objectif** : À l’issue du module, le participant pourra créer, tester et exécuter une chaîne simple (PromptTemplate + LLM + output parser) en moins de 10 minutes, en justifiant chaque composant.  

**Notions couvertes**  
- Architecture de LangChain : `Chain`, `LLM`, `PromptTemplate`, `BaseOutputParser`.  
- Gestion des prompts : interpolation, variables, `FewShotPromptTemplate`.  
- Types de LLM : OpenAI, Anthropic, Cohere, utilisation via `ChatOpenAI`.  
- Sérialisation et exécution synchrones/asynchrones.  
- Débogage avec `langchain.debug` et inspection du `run_id`.  

---

## Module 2 – Chaînes avancées et logique conditionnelle  

**Objectif** : Le participant sera capable de concevoir une chaîne composite intégrant au moins deux sous‑chaînes et une logique de routage conditionnelle, puis de la valider par des tests unitaires automatisés.  

**Notions couvertes**  
- `SequentialChain`, `RouterChain` et `ConditionalRouter`.  
- Création de composants personnalisés (`BaseChain`, `BaseTool`).  
- Passage de variables entre chaînes via le `input_dict`.  
- Intégration d’APIs externes (REST, GraphQL) avec `RequestsWrapper`.  
- Tests avec `pytest` et `langchain.testing`.  

---

## Module 3 – Mémoire, contexte et gestion des tokens  

**Objectif** : Le participant pourra implémenter une mémoire conversationnelle persistante (vector store + retriever) capable de restituer les 5 documents les plus pertinents en moins de 200 ms pour un contexte de 10 000 tokens.  

**Notions couvertes**  
- Types de mémoire : `ConversationBufferMemory`, `ConversationSummaryMemory`, `VectorStoreRetrieverMemory`.  
- Indexation avec `FAISS`, `Chroma`, `Pinecone`.  
- Stratégies de résumés (`LLMChain` + `map_reduce`).  
- Gestion du budget de tokens : `max_token_limit`, `truncate_prompt`.  
- Nettoyage et expiration des entrées de mémoire.  

---

## Module 4 – Introduction à LangGraph  

**Objectif** : Le participant pourra modéliser, coder et exécuter un graphe de décision

---

## Module 1 — contenu

## 1. Architecture de base de LangChain  

| Composant | Rôle | Classe principale |
|-----------|------|--------------------|
| **PromptTemplate** | Définit le texte du prompt avec des placeholders (`{variable}`) qui seront remplis à l’exécution. | `langchain.prompts.prompt.PromptTemplate` |
| **LLM** | Interface vers un modèle de langage (OpenAI, Anthropic, Cohere, …). Gère l’appel HTTP, le décodage et le suivi du `run_id`. | `langchain.llms.base.BaseLLM` (ex. `ChatOpenAI`) |
| **Chain** | Orchestration d’un ou plusieurs composants (prompt → LLM → output parser). Retourne un dictionnaire d’outputs. | `langchain.chains.base.Chain` (ex. `LLMChain`) |
| **BaseOutputParser** | Convertit la chaîne de caractères brute renvoyée par le LLM en une structure Python (dict, list, objet). | `langchain.schema.output_parser.BaseOutputParser` |
| **run_id** | Identifiant unique (UUID) généré à chaque exécution de chaîne, propagé aux logs et aux callbacks. |

### 1.1. PromptTemplate  

```python
from langchain.prompts import PromptTemplate

# Prompt avec deux variables d’entrée
template = """
You are a helpful assistant specialized in French grammar.
Given the sentence below, identify the grammatical gender of each noun
and return a JSON object with the noun as key and "masculine" or "feminine" as value.

Sentence: "{sentence}"
"""
prompt = PromptTemplate(
    input_variables=["sentence"],   # variables attendues
    template=template,
    template_format="jinja2",      # optionnel, permet les filtres Jinja
)
```

- **Interpolation** : `prompt.format(sentence="...")` renvoie le texte complet.  
- **Variables obligatoires** : si une clé manquante est fournie, `ValueError` est levé.  
- **Few‑Shot** : `FewShotPromptTemplate` ajoute un `examples` listé dans le prompt.

### 1.2. LLM – `ChatOpenAI`  

```python
from langchain.chat_models import ChatOpenAI

# Nécessite la variable d’environnement OPENAI_API_KEY
llm = ChatOpenAI(
    model_name="gpt-4o-mini",   # modèle disponible au moment de l’écriture
    temperature=0.0,            # pour des réponses déterministes
    max_tokens=500,             # limite de sortie du LLM
    streaming=False,            # désactive le streaming pour le premier test
)
```

- **Paramètres critiques**  
  - `temperature` : 0 → réponses les plus prévisibles, >0 → créativité.  
  - `max_tokens` : nombre de tokens que le LLM peut générer, impact direct sur le coût.  
  - `request_timeout` : défaut 600 s, à ajuster pour les appels longs.  

### 1.3. OutputParser – JSONParser  

```python
import json
from langchain.schema import output_parser

class JsonOutputParser(output_parser.BaseOutputParser):
    """Parse a JSON string returned by the LLM into a Python dict."""
    def parse(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON output: {exc}") from exc
```

- **Pourquoi un parser dédié ?**  
  - Le LLM renvoie toujours du texte brut. Sans parsing, le consommateur doit gérer les erreurs de formatage.  
  - Un `BaseOutputParser` permet d’intégrer le parsing dans le graphe de callbacks (debug, tracing).  

### 1.4. Chaîne complète – `LLMChain`  

```python
from langchain.chains import LLMChain

# Assemblage
chain = LLMChain(
    llm=llm,
    prompt=prompt,
    output_parser=JsonOutputParser(),   # optionnel, mais recommandé
    verbose=True,                       # active les logs détaillés
)
```

`LLMChain.__call__(**inputs)` attend les variables déclarées dans `prompt.input_variables`.  
Retour : `{"output": <parsed_object>, "run_id": <uuid>}`.

## 2. Exemple fonctionnel complet (synchronisé)

```python
# -*- coding: utf-8 -*-
"""
Exemple complet : extraire le genre grammatical des noms d’une phrase française.
Le script s’appuie uniquement sur LangChain (v0.2.6) et sur l’API OpenAI.
"""

from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.schema import output_parser
import json
import os

# 1️⃣ Prompt
prompt = PromptTemplate(
    input_variables=["sentence"],
    template="""
You are a French‑language expert. Identify every noun in the following sentence,
determine its grammatical gender, and return a JSON object where the key is the noun
and the value is either "masculine" or "feminine".

Sentence: "{sentence}"
""",
)

# 2️⃣ LLM
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.0,
    max_tokens=300,
)

# 3️⃣ Parser
class JsonParser(output_parser.BaseOutputParser):
    def parse(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM output is not valid JSON: {exc}") from exc

# 4️⃣ Chaîne
chain = LLMChain(
    llm=llm,
    prompt=prompt,
    output_parser=JsonParser(),
    verbose=True,      # affichage du prompt, du run_id, du temps d’exécution
)

# 5️⃣ Exécution
if __name__ == "__main__":
    # Exemple de

---

## Module 2 — contenu

## Module 2 – Chaînes avancées et logique conditionnelle  

### 2.1 Architecture des chaînes composites  

| Composant | Rôle | Interface clé |
|-----------|------|--------------|
| `SequentialChain` | Exécute plusieurs sous‑chaînes dans un ordre déterminé, transmet les sorties comme entrées de la suivante. | `run(input_dict: dict) → dict` |
| `RouterChain` / `ConditionalRouter` | Sélectionne dynamiquement la sous‑chaîne à exécuter en fonction d’une condition évaluée sur les entrées ou le contexte. | `route(input_dict: dict) → str` (nom de la chaîne) |
| `BaseChain` | Classe de base pour créer des chaînes personnalisées. Implémente `__call__` ou `run`. | `run(self, inputs: dict) → dict` |
| `BaseTool` | Encapsule une fonction ou un appel d’API réutilisable dans plusieurs chaînes. | `run(self, **kwargs) → Any` |

> **Note** : `RouterChain` ne doit pas être confondu avec `LLMRouterChain` (qui utilise le LLM pour le routage). Ici, le routage est purement logique (Python).

### 2.2 Création d’une sous‑chaîne personnalisée  

```python
from langchain.chains import BaseChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.schema import LLMResult

class SentimentAnalysisChain(BaseChain):
    """Renvoie le sentiment (positive/negative/neutral) d'un texte donné."""
    
    def __init__(self, llm: OpenAI, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template=(
                "Analyse le sentiment du texte suivant et répond uniquement avec "
                "one of: positive, negative, neutral.\n\nText: {text}"
            ),
        )

    @property
    def input_keys(self) -> set:
        return {"text"}

    @property
    def output_keys(self) -> set:
        return {"sentiment"}

    def _call(self, inputs: dict) -> dict:
        # 1️⃣ Interpolation du prompt
        formatted = self.prompt.format(**inputs)

        # 2️⃣ Appel LLM synchronisé
        raw_output: LLMResult = self.llm.invoke(formatted)

        # 3️⃣ Nettoyage de la réponse (strip, lower)
        sentiment = raw_output.content.strip().lower()
        if sentiment not in {"positive", "negative", "neutral"}:
            # Fallback sécurisé
            sentiment = "neutral"

        return {"sentiment": sentiment}
```

*Points de vérification*  

- `input_keys`/`output_keys` permettent à `SequentialChain` de résoudre les dépendances.  
- La méthode interne s’appelle `_call` (pas `run`) : `BaseChain.__call__` délègue à `_call`.  
- Le LLM retourné par `OpenAI` (ou `ChatOpenAI`) est un objet **synchronisé** ; pour une version asynchrone, remplacer `invoke` par `ainvoke`.

### 2.3 Chaîne composite avec routage conditionnel  

```python
from langchain.chains import SequentialChain, RouterChain, SimpleSequentialChain
from langchain.tools import RequestsWrapper
from typing import Literal

# 1️⃣ Définition de deux sous‑chaînes simples
class WeatherChain(BaseChain):
    """Récupère la météo d’une ville via l’API OpenWeatherMap."""
    def __init__(self, api_key: str):
        super().__init__()
        self.request = RequestsWrapper()
        self.api_key = api_key

    @property
    def input_keys(self):
        return {"city"}

    @property
    def output_keys(self):
        return {"weather"}

    def _call(self, inputs):
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={inputs['city']}&appid={self.api_key}&units=metric"
        )
        resp = self.request.run(url=url, method="GET")
        data = resp.json()
        description = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return {"weather": f"{description}, {temp}°C"}

class JokeChain(BaseChain):
    """Renvoie une blague aléatoire depuis l’API JokeAPI."""
    def __init__(self):
        super().__init__()
        self.request = RequestsWrapper()

    @property
    def input_keys(self):
        return set()

    @property
    def output_keys(self):
        return {"joke"}

    def _call(self, _):
        url = "https://v2.jokeapi.dev/joke/Any?type=single"
        resp = self.request.run(url=url, method="GET")
        return {"joke": resp.json()["joke"]}

# 2️⃣ Router logique (Python, pas LLM)
def route_by_intent(inputs: dict) -> Literal["weather", "joke"]:
    """Retourne le nom de la sous‑chaîne à exécuter."""
    intent = inputs.get("intent", "").lower()
    if intent == "weather":
        return "weather"
    elif intent == "joke":
        return "joke"
    else:
        # Valeur par défaut : blague
        return "joke"

router = RouterChain(
    route_function=route_by_intent,
    # Mapping du nom retourné vers l’objet chaîne
    destinations={
        "weather": WeatherChain(api_key="YOUR_OPENWEATHER_API_KEY"),
        "joke": JokeChain(),
    },
)

# 3️⃣ Chaîne principale qui orchestre le routage
class AssistantChain(BaseChain):
    """Orchestre le flux complet : intention → routage → exécution."""
    def __init__(self, router: RouterChain):
        super().__init__()
        self.router = router

    @property
    def input_keys(self

---

## Module 3 — contenu

## Module 3 – Mémoire, contexte et gestion des tokens  

### 1. Types de mémoire intégrés à LangChain  

| Mémoire | Description | Cas d’usage | Persistance |
|--------|--------------|-------------|-------------|
| `ConversationBufferMemory` | Stocke chaque échange sous forme de texte brut. | Chatbot à court terme où le fil complet doit être affiché. | En‑mémoire uniquement (volatile). |
| `ConversationSummaryMemory` | Résume le fil de discussion à chaque tour via un LLM. | Conversations longues où le coût de prompt doit être limité. | En‑mémoire, mais le résumé peut être stocké (ex. SQLite). |
| `VectorStoreRetrieverMemory` | Conserve les documents dans un store vectoriel et récupère les *k* plus pertinents via un retriever. | QA contextuel, assistance à la rédaction, recherche d’informations dans un corpus. | Persistance dépend du store (FAISS = fichier, Chroma = persisté, Pinecone = cloud). |

> **Vérifiable** : les classes mentionnées sont exportées depuis `langchain.memory` et implémentent l’interface `BaseMemory` (méthodes `load_memory_variables`, `save_context`).  

### 2. Indexation vectorielle  

#### 2.1 Choix du store  

| Store | Format | Scalabilité | Licence | Exemple d’instanciation |
|-------|--------|-------------|---------|--------------------------|
| **FAISS** | Index binaire sur disque (`.index`) | Jusqu’à plusieurs millions de vecteurs sur un seul nœud | BSD‑3 | `FAISS.from_texts(texts, embedding, index_path="faiss.index")` |
| **Chroma** | SQLite + fichiers binaires | Multi‑processus, support de collections | Apache‑2.0 | `Chroma(persist_directory="./chroma_db", embedding_function=embedding)` |
| **Pinecone** | Service cloud managé | Billions de vecteurs, réplication multi‑région | Commercial | `PineconeVectorStore.from_texts(texts, embedding, index_name="my-index")` |

> **Vérifiable** : les modules `langchain_community.vectorstores.faiss`, `langchain_community.vectorstores.chroma`, `langchain_community.vectorstores.pinecone` existent dans la distribution `langchain-community`.  

#### 2.2 Création d’un store FAISS à partir de textes  

```python
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path

# 1️⃣ Texte source – on suppose un corpus de 10 000 tokens réparti sur 200 documents
corpus_dir = Path("./data")
texts = [ (corpus_dir / f).read_text(encoding="utf-8") for f in corpus_dir.glob("*.txt") ]

# 2️⃣ Embedding – modèle d’OpenAI (coût token‑dépendant, 1536‑dim)
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")   # vérifiable via API docs

# 3️⃣ Construction du store (FAISS crée un index en RAM puis le sérialise)
vectorstore = FAISS.from_texts(texts, embeddings, metadatas=[{"source": p.name} for p in corpus_dir.glob("*.txt")])

# 4️⃣ Persistance sur disque (optionnel mais recommandé pour la mémoire persistante)
index_path = "./faiss_index"
vectorstore.save_local(index_path)          # crée index.faiss + docstore.pkl
```

*Commentaires*  

- `OpenAIEmbeddings` renvoie un vecteur de dimension 1536 pour le modèle `text-embedding-3-large`.  
- `FAISS.from_texts` accepte un paramètre `metadatas` qui sera renvoyé par le retriever.  
- La persistance se fait via `save_local`; le chargement ultérieur s’effectue avec `FAISS.load_local(index_path, embeddings)`.  

### 3.3 Retriever et récupération des *k* documents  

```python
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI

# Chargement du store persistant
vectorstore = FAISS.load_local("./faiss_index", OpenAIEmbeddings(model="text-embedding-3-large"))

# Retriever simple – renvoie les 5 documents les plus proches (cosine similarity)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# Exemple d’utilisation dans une chaîne
prompt = PromptTemplate.from_template(
    """Vous êtes un assistant qui répond aux questions en vous basant uniquement sur les passages suivants :

{context}

Question : {question}
Répondez en français, en citant les passages pertinents entre guillemets."""
)

llm = OpenAI(model="gpt-4o-mini")   # modèle de complétion texte
qa_chain = LLMChain(llm=llm, prompt=prompt)

def answer(question: str) -> str:
    # 1️⃣ Récupération du contexte
    docs = retriever.get_relevant_documents(question)   # -> List[Document]
    context = "\n\n".join(doc.page_content for doc in docs)
    # 2️⃣ Exécution du LLM
    return qa_chain.run({"question": question, "context": context})

print(answer("Comment fonctionne le protocole TCP ?"))
```

*Points clés*  

- `search_type="similarity"` utilise la distance cosinus par défaut ; `search_type="mmr"` permet la diversification.  
- Le temps de récupération dépend du nombre de vecteurs et du paramètre `k`. Sur un index FAISS de 200 000 vecteurs, `k=5` se situe généralement < 10 ms sur un CPU moderne.  

### 4. Gestion du budget de tokens  

#### 4.1 Calcul du nombre de tokens  

```python

---

## Module 4 — contenu

## Module 4 – Introduction à LangGraph  

### 1. Concepts fondamentaux  

| Concept | Description vérifiable | API LangGraph |
|--------|------------------------|---------------|
| **State** | Un dictionnaire JSON‑compatible qui circule entre les nœuds. Chaque nœud lit le même objet `state` et peut le muter. | `State` (type alias de `dict[str, Any]`) |
| **Node** | Fonction (sync ou async) qui reçoit `state` et renvoie un dict de mise à jour (`dict[str, Any]`). Le retour est fusionné dans le `state` global. | `@graph.node` décorateur ou `graph.add_node(name, fn)` |
| **Edge** | Relation dirigée `source → target`. Peut être **unconditionnelle** (`graph.add_edge`) ou **conditionnelle** (`graph.add_conditional_edge`). | `graph.add_edge`, `graph.add_conditional_edge` |
| **ConditionalRouter** | Fonction qui, à partir du `state`, renvoie le nom du nœud suivant. Utilisée avec `add_conditional_edge`. | `graph.add_conditional_edge(source, router, targets)` |
| **Loop** | Boucle explicite créée en ajoutant une arête du nœud de sortie vers un nœud antérieur. La condition de sortie doit être contrôlée par le router pour éviter les boucles infinies. | `graph.add_edge("node_a", "node_b")` + condition de sortie dans le router |
| **Graph execution** | L’appel `graph.invoke(state)` (sync) ou `await graph.ainvoke(state)` (async) démarre le flux à partir du nœud racine (`"__start__"`). Le résultat final est le `state` complet. | `graph.invoke`, `graph.ainvoke` |
| **Persistence** | Un graphe peut être sérialisé avec `graph.get_graph().model_dump_json()` et rechargé via `StateGraph.from_json`. | `graph.get_graph()`, `StateGraph.from_json` |
| **Debug** | Chaque transition crée un `run_id` unique; on peut récupérer le journal complet avec `graph.get_state(run_id)`. | `graph.get_state`, `graph.get_run_history` |

> **Note technique** : LangGraph est construit sur `langchain-core` ≥ 0.2.0. Les signatures de `invoke` et `ainvoke` sont identiques à celles des `Chain`.

---

### 2. Exemple complet – Chatbot décisionnel avec appel d’outil météo  

```python
# -*- coding: utf-8 -*-
"""
Exemple fonctionnel de LangGraph : 
- collecte d’une question utilisateur,
- décision d’utiliser l’outil météo ou de répondre directement,
- boucle de clarification (max 2 itérations),
- résumé final.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# ----------------------------------------------------------------------
# 1️⃣ Définition du schéma d’état partagé
# ----------------------------------------------------------------------
State = Dict[str, Any]  # alias explicite pour la lisibilité

# ----------------------------------------------------------------------
# 2️⃣ LLM et PromptTemplate (déclarés une fois, réutilisables)
# ----------------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

weather_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content="You are a helpful assistant that can call a weather API."),
        HumanMessage(content="{question}"),
    ]
)

weather_chain = weather_prompt | llm

# ----------------------------------------------------------------------
# 3️⃣ Nœuds du graphe
# ----------------------------------------------------------------------
def node_collect_question(state: State) -> State:
    """Premier nœud : récupère la question brute de l’utilisateur."""
    # Dans un vrai service, `state["input"]` provient du front‑end.
    return {"question": state["input"], "attempt": 0, "needs_tool": False}


def node_decide(state: State) -> State:
    """Analyse la question pour savoir si l’on doit appeler l’outil météo."""
    # Simple heuristique : présence du mot « météo » ou « temps ».
    q = state["question"].lower()
    if "météo" in q or "temps" in q:
        return {"needs_tool": True}
    return {"needs_tool": False}


def node_call_weather(state: State) -> State:
    """Appel simulé d’une API météo. Retourne un texte brut."""
    # Ici on ne touche pas à un vrai endpoint pour rester hors‑net.
    fake_response = {
        "Paris": "15 °C, partiellement nuageux, vent 12 km/h",
        "Lyon": "13 °C, pluie légère, vent 8 km/h",
    }
    # Extraction naïve de la ville (premier mot capitalisé)
    tokens = state["question"].split()
    city = next((t for t in tokens if t.istitle()), "Paris")
    weather = fake_response.get(city, "données indisponibles")
    return {"weather_info": f"Le temps à {city} : {weather}"}


def node_answer_direct(state: State) -> State:
    """Réponse directe via LLM (pas d’appel d’outil)."""
    response =

---

## Module 5 — contenu

## Module 5 – Graphes d’agents avancés : boucles, état persistant et intégration d’outils  

### 5.1. Concepts clés  

| Concept | Description vérifiable | API LangGraph |
|--------|------------------------|---------------|
| **StateGraph** | Graphe dont chaque exécution porte un dictionnaire d’état (`State`) partagé entre les nœuds. | `from langgraph.graph import StateGraph` |
| **Node (fonction)** | Fonction Python recevant `state: dict` et retournant un sous‑dict qui sera fusionné dans l’état global. | `@graph.node` ou `graph.add_node(name, fn)` |
| **Edge conditionnelle** | Transition basée sur la valeur d’une clé d’état (`state["status"]`). | `graph.set_conditional_edges(source, condition_fn, targets)` |
| **Loop** | Cycle d’exécution contrôlé par une condition d’arrêt (ex. `max_iterations` ou `state["done"]`). | Implémenté via edges conditionnelles qui reviennent au même nœud. |
| **Tool integration** | Un nœud peut appeler un `BaseTool` (ex. `RequestsWrapper`, `SQLDatabaseTool`). | `tool.run(**kwargs)` à l’intérieur du nœud. |
| **Persisted state** | L’état peut être sauvegardé dans un `BaseStore` (ex. `pickle`, `RedisStore`) entre deux runs du graphe. | `graph.save_state(state, store)` / `graph.load_state(store)` |
| **Streaming** | Retour incrémental des sorties de chaque nœud sans attendre la fin du graphe. | `graph.stream(state)` renvoie un générateur d’`Update` objects. |

### 5.2. Exemple complet : Agent de question‑réponse itératif avec rappel de confiance  

> **Objectif** :  
> - Recevoir une requête utilisateur.  
> - Interroger un `FAISS` retriever.  
> - Générer une réponse avec `ChatOpenAI`.  
> - Estimer la confiance via le score de similarité du document le plus pertinent.  
> - Si la confiance < 0.8, demander une clarification à l’utilisateur puis répéter (max 3 itérations).  

```python
# --------------------------------------------------------------
# Prérequis : pip install "langchain[all]" "langgraph" "faiss-cpu"
# --------------------------------------------------------------
import os
from typing import Any, Dict

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

from langgraph.graph import StateGraph, END

# ---------- 1. Initialise les composants ----------
# 1.1. LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 1.2. Vector store (FAISS) – on charge un index pré‑indexé
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.load_local(
    folder_path="data/faiss_index",
    embeddings=embeddings,
    index_name="documents",
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 1.3. Prompt de génération
prompt = PromptTemplate.from_template(
    """You are a concise assistant. Use only the information from the retrieved
    documents. Answer the user question below.

    Question: {question}
    Documents:
    {context}
    """
)

# ---------- 2. Définition du schéma d’état ----------
# L’état partagé entre les nœuds.
# - "question": texte fourni par l’utilisateur ou reformulé.
# - "retrieved_docs": list[Document] (rempli par le nœud retrieve).
# - "answer": texte généré.
# - "confidence": float (similarité du doc le plus proche).
# - "iterations": int (compteur de boucles).
# - "done": bool (signal de fin).
State = Dict[str, Any]

# ---------- 3. Fonctions de nœuds ----------
def retrieve(state: State) -> State:
    """Interroge le retriever et stocke les docs + score max."""
    docs = retriever.get_relevant_documents(state["question"])
    # Le retriever FAISS expose la distance via doc.metadata["distance"]
    max_score = max(1 - d.metadata.get("distance", 1) for d in docs)  # 1‑distance → similitude
    return {
        "retrieved_docs": docs,
        "confidence": max_score,
    }

def generate(state: State) -> State:
    """Construit le prompt et génère la réponse."""
    context = "\n---\n".join(d.page_content for d in state["retrieved_docs"])
    formatted = prompt.format(question=state["question"], context=context)
    answer = llm.invoke(formatted).content
    return {"answer": answer}

def decide(state: State