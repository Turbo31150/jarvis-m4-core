# LangChain & LangGraph pour Agents

> Référence `langchain-ia`

## Plan

## Module 1 – Fondamentaux de LangChain  

**Objectif** : À l’issue du module, le participant pourra créer, tester et exécuter une chaîne simple (PromptTemplate + LLM + output parser) rapidement, en justifiant chaque composant.  

**Notions couvertes**  
- Architecture de LangChain : `Chain`, `LLM`, `PromptTemplate`, `BaseOutputParser`.  
- Gestion des prompts : interpolation, variables, `FewShotPromptTemplate`.  
- Types de LLM : OpenAI, Anthropic, Cohere, utilisation via `ChatOpenAI`.  
- Sérialisation et exécution synchrones/asynchrones.  
- Débogage avec `langchain.debug` et inspection du `run_id`.  

---

## Module 2 – Chaînes avancées et logique conditionnelle  

**Objectif** : Le participant sera capable de concevoir une chaîne composite intégrant plusieurs sous‑chaînes et une logique de routage conditionnelle, puis de la valider par des tests unitaires automatisés.  

**Notions couvertes**  
- `SequentialChain`, `RouterChain` et `ConditionalRouter`.  
- Création de composants personnalisés (`BaseChain`, `BaseTool`).  
- Passage de variables entre chaînes via le `input_dict`.  
- Intégration d’APIs externes (REST, GraphQL) avec `RequestsWrapper`.  
- Tests avec `pytest` et `langchain.testing`.  

---

## Module 3 – Mémoire, contexte et gestion des tokens  

**Objectif** : Le participant pourra implémenter une mémoire conversationnelle persistante (vector store + retriever) capable de restituer les documents les plus pertinents rapidement pour un contexte de taille importante.  

**Notions couvertes**  
- Types de mémoire : `ConversationBufferMemory`, `ConversationSummaryMemory`, `VectorStoreRetrieverMemory`.  
- Indexation avec `FAISS`, `Chroma`, `Pinecone`.  
- Stratégies de résumés (`LLMChain` + `map_reduce`).  
- Gestion du budget de tokens : `max_token_limit`, `truncate_prompt`.  
- Nettoyage et expiration des entrées de mémoire.  

---

## Module 4 – Introduction à LangGraph  

**Objectif** : Le participant pourra modéliser, coder et exécuter un graphe de décision.

---

## Module 1 — contenu

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
    # Exemple de phrase
    sentence = "Le chat noir saute sur le canapé."
    result = chain.run(sentence=sentence)
    print("Résultat :", result)
```

---  

## Module 2 — contenu

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
from langchain.chains import SequentialChain, RouterChain
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
    def input_keys(self):
        return {"intent"}

    @property
    def output_keys(self):
        return {"result"}

    def _call(self, inputs: dict) -> dict:
        # Le router décide quelle