# Changelog

All notable changes to Casys RPG will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Architecture documentation
- Migration guides
- Validation rules documentation
- Test coverage for edge cases
- Initial project setup
- Basic game engine structure
- Four specialized LLM agents:
  - Rules Agent
  - Decision Agent
  - Narrator Agent
  - Trace Agent
- WebSocket-based real-time updates
- Redis state management
- Basic web interface
- Documentation complète de l'architecture frontend
- Nouvelles bonnes pratiques pour Svelte  

### Changed
- **CharacterManager**
  - Made save_character async to properly handle cache operations
  - Added character_id parameter with "current" as default
  - Made save_character_stats and update_character_stats async
  - Improved error handling and logging
  - Better character state management

- **StateManager**
  - Added CharacterManager as a dependency
  - Improved character creation and management
  - Better separation of concerns with CharacterManager
  - Updated tests to use proper mocks
  - Character state now managed by CharacterManager

- **WorkflowManager**
  - Extracted section transition logic to _handle_section_transition
  - Simplified start_workflow by delegating to StateManager
  - Better workflow state tracking and logging
  - Improved error handling
  - Added workflow metadata management

- **StoryGraph**
  - Refactored to use dictionary-based dependency injection
  - Managers and agents now passed as collections
  - Improved configuration handling
  - Better separation of concerns

- **Models**
  - Moved Choice model and validation to RulesModel
  - Simplified DecisionModel by removing choice handling
  - Added comprehensive validation for all choice types
  - Updated model relationships for better clarity
  - Simplified DecisionModel state management
  - Removed immutability constraints from individual models
  - Fixed Pydantic configuration to use model_config
  - Improved validation for conditions in DecisionModel
  - Better alignment with GameState architecture

- **Dependency Injection**
  - Standardized configuration-based injection
  - Removed direct manager arguments from constructors
  - Improved testability and flexibility

- **GameState**
  - Added `keep_if_not_empty` reducer function for LangGraph fan-in
    - Returns `b` only if not empty, otherwise keeps `a`
    - Used to preserve important state values during merging
  - Modified field annotations in GameStateBase:
    - Changed `session_id` and `game_id` from `first_not_none` to `keep_if_not_empty`
    - Ensures IDs are only overwritten with non-empty values
  - Modified field annotations in GameStateInput:
    - Changed `section_number` and `player_input` to use `keep_if_not_empty`
    - Better preservation of input state during merging
  - Updated GameStateOutput model fields:
    - Changed `decision`, `trace`, and `character` to use `first_not_none` annotation
    - All content models now consistently use `first_not_none` for merging
  - Simplified GameState.with_updates logging:
    - Removed verbose narrative content logging
    - Added focused debug logging for session_id and section_number

- Optimized state management in GameState
- Simplified model merging strategy using take_last_value for DecisionModel
- Improved node data handling with take_from_node for NarratorModel and RulesModel

- Refactoring des services pour utiliser des objets simples au lieu de classes
- Optimisation de la gestion d'état avec useResource$ et useTask$
- Amélioration de la gestion WebSocket
- Simplification de la configuration API

### Fixed
- **GameConfig**
  - Fixed import paths and module organization
  - Improved configuration validation
  - Better error messages for invalid configs

- **Factory Methods**
  - Removed redundant model factory methods
  - Using direct constructors for simple models
  - Factory methods reserved for complex objects

- Problèmes de sérialisation Qwik
- Gestion des erreurs WebSocket
- Navigation entre les sections
- Removed incompatible model_post_init usage
- Corrected Pydantic configuration format
- Fixed model validation workflow
- Character save operations now properly async
- Section transition handling in workflow
- Character state persistence
- Workflow state transitions
- Error handling in character operations
- Fixed state merging issues in parallel node execution
- Corrected player_input handling in decision processing
- Fixed None value handling in take_from_node function

### Architecture
- Improved dependency injection patterns
- Better separation of concerns in models
- More consistent configuration handling
- Cleaner model relationships
- Better alignment with GameState immutability pattern
- Clearer separation of responsibilities:
  - GameState handles immutability
  - Models focus on validation
- Improved model update workflow

### Documentation
- Updated architecture documentation
- Added migration guides
- Improved code comments
- Added validation rules documentation

### Testing
- Added comprehensive Choice validation tests
- Updated fixtures for new model structure
- Improved test organization
- Better test coverage for edge cases
- Updated model tests to reflect mutable state
- Added tests for model updates and validation
- Improved test coverage for edge cases

### Removed
- Pattern Singleton des services
- useVisibleTask$ remplacé par useTask$
- Classes GameService et WebSocketService
- Code legacy non utilisé

### Technical Debt
- Consider adding character versioning
- Add more comprehensive error states
- Improve cache invalidation strategy
- Add performance metrics
- Consider implementing character templates

## [0.1.0] - 2024-12-31
### Added
- Initial release with core functionality:
  - Multi-agent system architecture
  - Core models and validation
  - Basic game engine
  - Test suite foundation
  - Configuration system
  - Model factories
  - Manager protocols
