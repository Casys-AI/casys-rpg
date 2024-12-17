# Test Documentation: Feedback System

## Overview
This document details the test suite for the Feedback System component, which handles user feedback collection, storage, and validation during gameplay sessions.

## Test Infrastructure

### Fixtures

#### `feedback_dir`
**Purpose**: Creates isolated test environment
**Setup**:
```python
feedback_path = tmp_path / "data" / "feedback"
feedback_path.mkdir(parents=True)
```
**Usage**: Provides temporary storage for test feedback files

### Test Environment
- Uses `pytest`'s temporary path functionality
- Implements path redirection via `monkeypatch`
- Maintains UTF-8 encoding support
- Ensures test isolation

## Detailed Test Cases

### 1. Basic Feedback Saving (`test_save_feedback`)
**Purpose**: Verify core feedback storage functionality

#### Input Data:
```python
feedback = "Super jeu !"
previous_section = {
    "content": "# Section 1\nContenu de test"
}
user_response = "Je vais à gauche"
current_section = 2
```

#### Validations:
1. File Creation:
```python
assert os.path.exists(filepath)
```

2. Content Structure:
```python
assert "# Feedback sur décision" in content
assert "Super jeu !" in content
assert "Section actuelle : 2" in content
assert "Je vais à gauche" in content
assert "# Section 1" in content
```

#### File Format:
```markdown
# Feedback sur décision
Section actuelle : 2

## Réponse utilisateur
Je vais à gauche

## Feedback
Super jeu !

## Section précédente
# Section 1
Contenu de test
```

### 2. Feedback Validation (`test_feedback_validation`)
**Purpose**: Test system resilience with minimal input

#### Test Cases:
1. Empty Feedback:
```python
empty_feedback = ""
previous_section = {"content": "Test"}
user_response = "Test"
current_section = 1
```

#### Validations:
- File creation despite empty feedback
- Minimal content structure
- Section number preservation
```python
assert os.path.exists(filepath)
assert "Section actuelle : 1" in content
```

### 3. Special Characters (`test_feedback_special_characters`)
**Purpose**: Verify Unicode and special character support

#### Test Input:
```python
feedback = "Très bien ! 🎮 J'aime les émojis 👍"
user_response = "Test avec émojis 🎲"
```

#### Validations:
1. Character Preservation:
```python
assert "Très bien !" in content
assert "🎮" in content
assert "émojis 🎲" in content
```

2. Encoding Checks:
- UTF-8 encoding
- Emoji support
- Accented character handling

## File Structure
```
data/
└── feedback/
    └── feedback_[timestamp].md
```

## Content Format
```markdown
# Feedback sur décision
Section actuelle : [section_number]

## Réponse utilisateur
[user_response]

## Feedback
[feedback_content]

## Section précédente
[previous_section_content]
```

## Error Handling
- File system access errors
- Encoding issues
- Invalid input data
- Missing directories

## Best Practices
- Atomic file operations
- Proper file closing
- UTF-8 encoding enforcement
- Directory structure validation
