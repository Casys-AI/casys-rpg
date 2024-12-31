# Test Changelog

## 2024-12-31

### Changed
- **test_story_graph.py**
  - Updated story_graph fixture to use managers and agents dictionaries
  - Fixed initialization test to check for manager and agent collections
  - Aligned with StoryGraph's new dependency injection pattern

### Fixed
- **test_rules_model.py**
  - Added comprehensive Choice validation tests
  - Updated sample_rules_model fixture with valid choices
  - Fixed NextActionType import path
  - Added tests for all choice types (direct, conditional, dice, mixed)

- **test_decision_model.py**
  - Removed obsolete choice-related tests
  - Updated tests for immutability and serialization
  - Added tests for conditions field
  - Fixed model validation tests

### Architectural Changes
- Using direct constructors for models instead of factory methods
- Proper configuration-based dependency injection in GameFactory
- Dictionary-based dependency injection in StoryGraph
- Choice validation moved from DecisionModel to RulesModel

### Migration Notes
- Use direct model constructors instead of factory methods
- Access LLM through agent config (`agent.config.llm`)
- Inject dependencies through config objects in GameFactory
- Use dictionaries for manager and agent injection in StoryGraph
- Handle choices in RulesModel instead of DecisionModel
