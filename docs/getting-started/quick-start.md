# Quick Start Guide

This guide will help you get up and running with Casys RPG quickly.

## Prerequisites

Before starting, ensure you have:
- Python 3.8 or higher installed
- pip package manager
- OpenAI API key

## Installation

1. Install Casys RPG:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your environment variables:
   ```bash
   # Windows
   set OPENAI_API_KEY=your_api_key_here
   
   # Linux/MacOS
   export OPENAI_API_KEY=your_api_key_here
   ```

## Basic Usage

1. Start the game server:
   ```python
   python main.py
   ```

2. Access the web interface at `http://localhost:8000`

## Example Game Session

Here's a simple example of how to use Casys RPG:

```python
from casys_rpg.game import GameSession

# Initialize game session
game = GameSession()

# Start new game
game.start_new_game()

# Make a decision
game.process_decision("I want to explore the cave")

# Roll dice for combat
game.roll_dice("combat")
```

## Next Steps

- Read the [Architecture Overview](../architecture/overview.md) to understand the system
- Check out the [API Documentation](../api/overview.md) for detailed endpoint information
- Learn about the [Agents](../agents/overview.md) that power the game
