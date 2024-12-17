# Test Documentation: Rules Agent

## Overview
This document details the test suite for the Rules Agent component, which analyzes game content to determine rules, required actions, and possible choices.

## Test Infrastructure

### Mock Components
- `MockLLM`: Simulates LLM responses with predefined rule structures
  - Returns combat-oriented responses for testing
  - Includes logging for debugging

### Fixtures
- `event_loop`: Manages async test execution
- `rules_agent`: Configures agent with gpt-4o-mini model
- `clean_cache`: Manages test cache directory

## Detailed Test Cases

### 1. Basic Functionality (`test_rules_agent_basic`)
**Purpose**: Verify basic agent response structure
**Input**:
```python
{
    "state": {
        "section_number": 1,
        "current_section": {
            "content": "Test content"
        }
    }
}
```
**Validations**:
- Presence of state object
- Rules field in state
- Needs_dice field in rules

### 2. Cache Management (`test_rules_agent_cache`)
**Purpose**: Verify disk cache functionality
**Process**:
1. First call:
   - Analyzes content
   - Stores in cache
2. Second call:
   - Retrieves from cache
   - Validates consistency
**Validations**:
- Cache persistence
- Response consistency between calls
- Rule structure preservation

### 3. Cache Error Handling (`test_rules_agent_cache_error`)
**Purpose**: Test cache error management
**Test Case**:
- Section number: 999 (non-existent)
- Empty content
**Expected Error**:
- "No content found for section 999"
**Validations**:
- Error presence in state
- Correct error message
- Proper error structure

### 4. Dice Roll Detection (`test_rules_agent_dice_handling`)
**Purpose**: Verify dice requirement analysis
**Test Content**:
```
Vous devez faire un jet de dés de combat.
Si vous réussissez, allez à la section 2.
```
**Validations**:
- needs_dice = true
- dice_type = "combat"
- next_sections includes 2
- Proper rule structure

### 5. Invalid Section Handling (`test_rules_agent_invalid_section`)
**Purpose**: Test invalid section number handling
**Test Case**:
- Section number: -1
**Validations**:
- Error presence
- Proper error message
- State structure integrity

### 6. Content Analysis (`test_rules_agent_analyze_content`)
**Purpose**: Test rule extraction from content
**Test Content**:
```
Vous êtes dans une pièce sombre. Vous pouvez:
- Allumer une torche et aller au [[2]]
- Continuer dans l'obscurité vers le [[3]]
```
**Validations**:
- Choice extraction
- Section number parsing
- Rule structure completeness

### 7. Invalid Input Handling (`test_rules_agent_invalid_input`)
**Purpose**: Test empty state handling
**Test Case**:
- Empty state object
**Validations**:
- Error presence
- "No section number provided" message
- State integrity

### 8. State Transmission (`test_rules_agent_state_transmission`)
**Purpose**: Verify complete rule analysis and state management
**Test Content**: Complex combat scenario with multiple outcomes
**Validations**:
- Dice requirement detection
- Combat type identification
- Multiple section paths (2 and 3)
- Complete rule structure:
  - needs_dice
  - dice_type
  - next_sections
  - conditions
  - choices

## Configuration Details
- Model: gpt-4o-mini
- Temperature: 0 (deterministic responses)
- Cache Directory: data/rules/cache
- Environment: Uses .env for API configuration
