# Contributing to Casys RPG

Thank you for your interest in contributing to Casys RPG! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Submitting Changes](#submitting-changes)

## Code of Conduct

This project follows a Code of Conduct that all contributors are expected to adhere to. Please read [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/casys-rpg.git
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/Casys-AI/casys-rpg.git
   ```

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the environment:
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/MacOS
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Making Changes

### Branch Naming Convention

- Feature: `feature/description`
- Bug fix: `fix/description`
- Documentation: `docs/description`
- Performance: `perf/description`

### Coding Standards

We follow these principles:
- SOLID Design Principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)

### Code Style

- Follow PEP 8
- Use type hints
- Document all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

Example:
```python
from typing import Optional

def process_section(
    section_number: int,
    content: Optional[str] = None
) -> bool:
    """Process a game section.
    
    Args:
        section_number: Section identifier
        content: Optional section content
        
    Returns:
        bool: True if processing successful
    """
    # Implementation
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rules_agent.py

# Run with coverage
pytest --cov=casys_rpg tests/
```

### Writing Tests

1. Place tests in the `tests/` directory
2. Follow the naming convention: `test_*.py`
3. Use descriptive test names
4. Include both positive and negative tests
5. Mock external dependencies

Example:
```python
def test_process_section_valid_input():
    # Arrange
    section_number = 1
    content = "Test content"
    
    # Act
    result = process_section(section_number, content)
    
    # Assert
    assert result is True
```

## Documentation

### Code Documentation

- Use docstrings for all public APIs
- Follow Google style docstrings
- Include type hints
- Document exceptions

### Project Documentation

- Update relevant .md files
- Keep the API documentation current
- Add examples for new features
- Update the changelog

## Submitting Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/my-feature
   ```

4. Create a Pull Request

### Pull Request Guidelines

- Use the PR template
- Reference any related issues
- Include tests
- Update documentation
- Follow commit message convention

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

Example:
```
feat(rules): add dice roll validation

- Add input validation for dice rolls
- Implement result calculation
- Add unit tests

Closes #123
```

## Review Process

1. Automated checks must pass
2. Code review by maintainers
3. Documentation review
4. Testing verification
5. Final approval

## Getting Help

- Create an issue
- Join our Discord server
- Check the documentation
- Contact maintainers

Thank you for contributing to Casys RPG!
