# Changelog

All notable changes to Casys RPG will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Basic game engine structure
- Four specialized LLM agents:
  - Rules Agent
  - Decision Agent
  - Narrator Agent
  - Trace Agent
- WebSocket-based real-time updates
- Redis state management
- FAISS-based rules indexing
- Basic web interface
- Documentation complète de l'architecture frontend
- Nouvelles bonnes pratiques pour Qwik

### Changed
- None
- Refactoring des services pour utiliser des objets simples au lieu de classes
- Optimisation de la gestion d'état avec useResource$ et useTask$
- Amélioration de la gestion WebSocket
- Simplification de la configuration API

### Deprecated
- None

### Removed
- None
- Pattern Singleton des services
- useVisibleTask$ remplacé par useTask$
- Classes GameService et WebSocketService

### Fixed
- None
- Problèmes de sérialisation Qwik
- Gestion des erreurs WebSocket
- Navigation entre les sections

### Security
- None

## [0.1.0] - 2024-12-22

### Added
- Initial release
- Basic game functionality
- Agent system architecture
- Documentation structure

## [0.1.0] - 2024-12-27

### Added
- Structure initiale du projet
- Système d'agents LangChain
- Interface utilisateur Qwik
- Documentation de base

### Changed
- Première implémentation des composants
- Configuration initiale

### Removed
- Code legacy non utilisé
