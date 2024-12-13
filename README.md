# Livre dont vous êtes le héros - Système de jeu interactif

## Description
Application interactive permettant de jouer à un livre dont vous êtes le héros, avec gestion intelligente des règles et des décisions grâce à des agents LLM.

## Architecture

Le système utilise quatre agents spécialisés avec LangChain :

### 1. RulesAgent (Agent de Règles)
- Utilise RAG (Retrieval Augmented Generation) pour analyser les règles
- Indexe toutes les règles avec FAISS pour une recherche sémantique
- Pour chaque section :
  - Analyse les règles spécifiques
  - Trouve des règles similaires dans d'autres sections
  - Combine les règles pour une meilleure compréhension
- Retourne une analyse structurée (JSON) :
  ```json
  {
    "needs_dice_roll": true|false,
    "dice_type": "chance"|"combat"|null,
    "conditions": ["condition1", "condition2"],
    "next_sections": [1, 2, 3],
    "rules_summary": "Résumé des règles"
  }
  ```

### 2. DecisionAgent (Agent de Décision)
- Interprète la réponse de l'utilisateur
- Utilise l'analyse fournie par le RulesAgent
- Vérifie que la section choisie est valide
- Se concentre uniquement sur la logique de décision

### 3. NarratorAgent (Agent Narrateur)
- Lit les sections du livre
- Formate le texte pour l'affichage
- Gère la présentation du contenu

### 4. TraceAgent (Agent de Trace)
- Enregistre chaque décision avec son contexte
- Conserve l'historique des parties
- Permet de reprendre une partie en cours

## Workflow

1. **Initialisation**
   - Construction de l'index FAISS des règles
   - Création des agents avec leurs dépendances

2. **Boucle de jeu**
   ```mermaid
   graph TD
      A[Section actuelle] --> B[RulesAgent analyse]
      B --> C[Affichage section]
      C --> D[Réponse utilisateur]
      D --> E[DecisionAgent décide]
      E --> F[TraceAgent enregistre]
      F --> A
   ```

3. **Analyse des règles**
   - RulesAgent combine :
     - Règles de la section actuelle
     - Règles similaires trouvées par RAG
   - Fournit un contexte enrichi pour la décision

4. **Prise de décision**
   - DecisionAgent utilise :
     - Réponse de l'utilisateur
     - Analyse des règles
     - Sections possibles

## Structure des fichiers

```
.
├── agents/
│   ├── rules_agent.py    # RAG + Analyse des règles
│   ├── decision_agent.py # Logique de décision
│   ├── narrator_agent.py # Lecture des sections
│   ├── trace_agent.py    # Historique
│   └── story_graph.py    # Coordination
├── data/
│   ├── sections/        # Texte du livre
│   └── rules/          # Règles par section
├── app.py              # Interface Streamlit
└── requirements.txt    # Dépendances
```

## Installation

1. **Prérequis**
   - Python 3.8+
   - pip

2. **Installation**
   ```bash
   # Cloner le dépôt
   git clone [url-du-repo]
   cd [nom-du-repo]

   # Installer les dépendances
   pip install -r requirements.txt
   ```

3. **Configuration**
   - Créer un fichier `.env` :
     ```
     OPENAI_API_KEY=votre-clé-api
     ```

4. **Lancement**
   ```bash
   streamlit run app.py
   ```

## Dépendances principales

- LangChain : Agents LLM
- FAISS : Indexation vectorielle
- OpenAI : Embeddings et LLM
- Streamlit : Interface utilisateur

## Documentation des spécifications

### Modèles LLM
- Utilisation de `gpt-4o-mini` pour tous les agents
- Température :
  - RulesAgent : 0 (déterministe)
  - DecisionAgent : 0.7 (créativité contrôlée)

### Index vectoriel
- FAISS avec métrique L2
- Dimension : 1536 (OpenAI embeddings)
- Mise à jour : à chaque lancement

### Format des règles
- Fichiers Markdown
- Un fichier par section : `section_X_rule.md`
- Structure :
  ```markdown
  # Règles Section X
  - Conditions : [...]
  - Actions possibles : [...]
  - Sections suivantes : [...]
  ```

Cette documentation est mise à jour régulièrement pour refléter les changements dans l'architecture et l'implémentation.
