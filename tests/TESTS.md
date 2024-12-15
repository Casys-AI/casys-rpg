# 🎲 Spécifications Fonctionnelles Testées

## 1. Gestion du Flux de Jeu (StoryGraph)

### Spécifications Couvertes
- Navigation linéaire entre les sections
- Gestion des états de jeu (attente, action, résolution)
- Intégration des jets de dés dans le flux
- Traçabilité des décisions et actions
- Mise à jour des statistiques en temps réel

### Spécifications Non Couvertes
- Navigation non-linéaire complexe
- Sauvegarde/Chargement de partie
- Gestion des points de sauvegarde
- Retour en arrière dans l'histoire

## 2. Système de Décision

### Spécifications Couvertes
- Interprétation des réponses utilisateur simples
- Validation des choix de section
- Gestion des jets de dés obligatoires
- Conditions de progression basiques

### Spécifications Non Couvertes
- Conditions de progression complexes
- Décisions basées sur l'inventaire
- Choix conditionnels multiples
- Impact des statistiques sur les décisions

## 3. Système de Narration

### Spécifications Couvertes
- Lecture des sections de texte
- Formatage basique du contenu
- Gestion des sections manquantes
- Cache des sections fréquentes

### Spécifications Non Couvertes
- Contenu dynamique basé sur l'état
- Variations narratives selon les stats
- Contenu multimédia
- Localisation du contenu

## 4. Système de Règles

### Spécifications Couvertes
- Détection des besoins en jets de dés
- Types de jets (combat, chance)
- Règles de progression simples
- Cache des règles fréquentes

### Spécifications Non Couvertes
- Règles de combat complexes
- Système d'inventaire
- Règles conditionnelles avancées
- Modificateurs de stats

## 5. Système d'Événements

### Spécifications Couvertes
- Communication entre agents
- Historique des événements
- Filtrage des événements
- Intégrité des données

### Spécifications Non Couvertes
- Événements conditionnels
- Chaînes d'événements
- Événements temporels
- Événements externes

## 6. Système de Feedback

### Spécifications Couvertes
- Collecte de feedback basique
- Validation des entrées
- Stockage simple

### Spécifications Non Couvertes
- Analyse du feedback
- Feedback contextuel
- Suggestions basées sur le feedback
- Métriques de jeu

## 7. Système de Traçage

### Spécifications Couvertes
- Enregistrement des décisions
- Suivi des statistiques de base
- Historique des actions
- Persistance simple

### Spécifications Non Couvertes
- Analyse du parcours
- Statistiques avancées
- Achievements
- Profils de joueur

## 8. Pydantic Configuration

All agent classes inherit from `pydantic.BaseModel` and use the following configuration:

```python
model_config = ConfigDict(arbitrary_types_allowed=True)
```

This configuration is required to allow Pydantic to handle non-standard types like `logging.Logger` that are used throughout the codebase.

The configuration is applied to:
- GameState
- RulesAgent  
- DecisionAgent
- NarratorAgent
- TraceAgent

## Historique des Tests

### Version 1.0.0 (15/12/2023)
- Tests initiaux du StoryGraph
- Tests basiques des agents
- Structure de test simple

### Version 1.1.0 (15/12/2023)
- Ajout des tests de gestion d'erreurs
- Amélioration des assertions
- Introduction du MockEventBus

### Version 1.2.0 (15/12/2023)
- Refactoring complet des tests
- Meilleure gestion des états
- Tests plus précis pour chaque agent

## Tests du StoryGraph

### Structure des Tests

Les tests du StoryGraph vérifient les aspects suivants :

1. **Chargement Initial**
   - Chargement correct de la section initiale
   - Présence du contenu narratif
   - Vérification des règles initiales

2. **Réponses Utilisateur**
   - Structure de la décision :
     ```python
     {
         "next_section": int | None,
         "awaiting_action": bool,
         "conditions": list[str],
         "rules_summary": str
     }
     ```
   - Validation des conditions de transition
   - Gestion des attentes d'action

3. **Lancers de Dés**
   - Traitement des résultats de dés
   - Mise à jour des conditions
   - Transition vers la section suivante

4. **Événements**
   - Émission correcte des événements
   - Intégration avec le TraceAgent
   - Mise à jour des statistiques

### Points Clés Testés

- Validation de la structure complète des réponses
- Gestion des conditions et des transitions
- Intégration des différents agents
- Traçage des actions et statistiques

## Tests StoryGraph (Détails)

### test_story_graph_initial_state
**Objectif** : Vérifier l'initialisation correcte du StoryGraph et le flux initial.
**Vérifie** :
- Chargement du contenu initial
- Configuration des règles
- État de décision initial
- Historique des états

```python
async def test_story_graph_initial_state(event_bus):
    # Vérification de l'état initial
    assert state1.get("content") == "Test content for section 1"
    assert state1.get("rules", {}).get("needs_dice") is True
    # Vérification de la décision
    assert state2["decision"].get("awaiting_action") == "choice"
```

### test_story_graph_user_response_with_dice
**Objectif** : Tester le flux avec un lancer de dés requis.
**Vérifie** :
- Détection du besoin de dés
- Type de dés correct
- Résultat du lancer
- Mise à jour de l'état

```python
async def test_story_graph_user_response_with_dice(event_bus):
    # Vérification du besoin de dés
    assert state1.get("rules", {}).get("needs_dice") is True
    assert state1.get("rules", {}).get("dice_type") == "normal"
    # Vérification du résultat
    assert state3.get("trace", {}).get("last_action") == "dice_roll"
```

### test_story_graph_user_response_without_dice
**Objectif** : Tester le flux sans lancer de dés.
**Vérifie** :
- Progression normale
- Choix de section
- État de trace
- Historique des états

```python
async def test_story_graph_user_response_without_dice(event_bus):
    # Vérification de la progression
    assert state1.get("rules", {}).get("needs_dice") is False
    # Vérification du choix
    assert state3.get("trace", {}).get("selected_section") == 2
```

### test_story_graph_error_handling
**Objectif** : Vérifier la gestion des erreurs.
**Vérifie** :
- Capture des exceptions
- Message d'erreur correct
- État d'erreur
- Historique préservé

```python
async def test_story_graph_error_handling(event_bus):
    # Vérification de l'erreur
    assert "error" in final_state
    assert "Test error" in str(final_state["error"])
```

## Mocks et Fixtures

### MockEventBus
- Simule le bus d'événements
- Garde un historique des états
- Permet la vérification des transitions

### MockAgent
- Agent de base pour les tests
- Retourne des résultats prédéfinis
- Simule le comportement asynchrone

### MockErrorAgent
- Simule des erreurs contrôlées
- Permet de tester la gestion d'erreurs
- Vérifie la robustesse du système

## Points d'Attention

### Couverture des Tests
✅ **Couvert** :
- Flux de base
- Gestion des dés
- Gestion des erreurs
- États multiples

❌ **À Améliorer** :
- Tests de performance
- Cas limites
- Conditions complexes
- États concurrents

### Bonnes Pratiques
1. Utiliser des assertions explicites
2. Vérifier les états intermédiaires
3. Tester les erreurs spécifiques
4. Maintenir l'historique des états

### Maintenance
- Mettre à jour les tests avec les nouvelles fonctionnalités
- Vérifier la couverture régulièrement
- Documenter les changements
- Maintenir la cohérence des mocks

## Points Critiques à Noter

### Gestion des Dés
✅ Implémenté :
- Jets simples
- Types de jets (combat/chance)
- Résultats déterministes

❌ Non implémenté :
- Modificateurs complexes
- Jets multiples
- Jets conditionnels

### Progression du Jeu
✅ Implémenté :
- Navigation section par section
- Conditions simples
- État de jeu basique

❌ Non implémenté :
- Branches multiples
- Points de non-retour
- États complexes

### Statistiques
✅ Implémenté :
- Stats de base (Habileté, Chance)
- Modifications simples
- Persistance basique

❌ Non implémenté :
- Stats dérivées
- Équipement
- Compétences
