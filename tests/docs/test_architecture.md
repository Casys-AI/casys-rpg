# Test Architecture Documentation

## Technical Components

### 1. Factory System

Le système de Factory est organisé en trois niveaux hiérarchiques :

#### BaseFactory
Fournit l'infrastructure de base pour la création d'objets avec :
- Gestion du cache
- Configuration par défaut
- Méthodes de création abstraites

#### ModelFactory
Spécialisé dans la création d'instances de modèles pour les tests :
- Hérite de BaseFactory
- Utilisé dans `tests/conftest.py` comme fixture globale
- Crée des instances valides avec des valeurs par défaut

#### GameFactory
Gère la création du système de jeu complet :
- Injection de dépendances automatique
- Validation des composants créés
- Cache intelligent des instances

```mermaid
graph TD
    A[BaseFactory] --> B[ModelFactory]
    A --> C[GameFactory]
    B --> D[test fixtures]
    C --> E[game system]
```

### 2. Protocol System

Le système de protocoles définit les contrats d'interface pour tous les composants :

#### Hiérarchie
```mermaid
graph TD
    A[BaseProtocol] --> B[ManagerProtocols]
    A --> C[AgentProtocols]
    B --> D[StateManagerProtocol]
    B --> E[CacheManagerProtocol]
    C --> F[StoryGraphProtocol]
    C --> G[RulesAgentProtocol]
```

#### Caractéristiques Clés
- Définition des contrats d'interface pure
- Support des opérations asynchrones
- Validation des types au niveau protocole
- Pas d'implémentation concrète

Exemple minimal :
```python
class StateManagerProtocol(Protocol):
    """Illustre la structure d'un protocole."""
    async def get_state(self) -> GameState: ...
    async def update_state(self, state: GameState) -> None: ...
```

### 3. Type System

Le système de types s'organise en couches :

#### Structure
1. Types de Base
   - Enums personnalisés
   - Modèles de base avec validation
   - Types primitifs étendus

2. Types Composés
   - États de jeu
   - Configurations
   - Résultats de validation

3. Types Utilitaires
   - Validateurs
   - Convertisseurs
   - Types génériques

```mermaid
graph TD
    A[Base Types] --> B[Game Types]
    A --> C[Config Types]
    B --> D[State Types]
    C --> E[Manager Config]
    C --> F[Agent Config]
```

### 4. Dependency System

Le système de dépendances gère l'injection et la résolution des composants :

#### Architecture
```mermaid
graph TD
    A[GameFactory] --> B[StateManager]
    A --> C[CacheManager]
    B --> C
    B --> D[StorageConfig]
    C --> D
```

#### Caractéristiques
- Résolution automatique des dépendances
- Configuration via décorateurs
- Support des singletons et de la création paresseuse
- Validation des dépendances circulaires

Exemple d'utilisation :
```python
@configured_dependency(singleton=True)
class StateManager:
    """Illustre l'injection de dépendances."""
    def __init__(self, cache_manager: CacheManagerProtocol):
        self.cache_manager = cache_manager
```

### 5. Test Infrastructure

L'infrastructure de test fournit :

#### Composants Clés
1. Gestion des Fixtures
   - Hiérarchie de fixtures
   - Portée configurable
   - Nettoyage automatique

2. Mock System
   - Mocks basés sur les protocoles
   - Réponses configurables
   - Validation des appels

3. Métriques
   - Collecte de métriques
   - Rapports de performance
   - Analyse des tests

#### Organisation
```
tests/
├── agents/              # Tests des agents
├── managers/           # Tests des managers
├── models/             # Tests des modèles
└── conftest.py         # Fixtures globales
```
