# Getting Started

!!! abstract "Quick Start Guide"
    This guide will help you get started with CASYS RPG, from installation to creating your first game.

## Prerequisites

!!! info "Requirements"
    * Python 3.10 or higher
    * Node.js 18 or higher
    * Git

## Installation

=== "Using pip"

    ```bash
    pip install casys-rpg
    ```

=== "From source"

    ```bash
    git clone https://github.com/yourusername/casys-rpg.git
    cd casys-rpg
    pip install -e .
    ```

## Basic Configuration

!!! example "Configuration File"
    ```yaml
    # config.yml
    game:
      name: "My First Adventure"
      version: "1.0.0"
    
    agents:
      story_graph:
        model: "gpt-4o-mini"
      rules:
        enabled: true
      narrator:
        style: "descriptive"
    ```

## First Steps

1. **Create a New Game**
   ```bash
   casys-rpg init my-game
   cd my-game
   ```

2. **Configure Your Game**
   Edit `config.yml` with your game settings

3. **Start Development Server**
   ```bash
   casys-rpg dev
   ```

## Next Steps

* Learn about the [Core Concepts](../concepts/index.md)
* Explore [Advanced Features](../advanced/index.md)
* Check our [Technical Documentation](../../architecture/index.md)

## Common Issues

!!! warning "Troubleshooting"
    * Check Python version compatibility
    * Verify Node.js installation
    * Ensure all dependencies are installed

!!! tip "Development Tips"
    * Use VSCode with our extension
    * Enable debug logging
    * Join our Discord community

## Examples

=== "Basic Game"
    ```python
    from casys_rpg.agents import StoryGraphAgent, RulesAgent, NarratorAgent
    from casys_rpg.managers import AgentManager, StateManager
    
    # Initialize managers
    state_mgr = StateManager()
    agent_mgr = AgentManager(state_mgr)
    
    # Initialize agents
    story = StoryGraphAgent()
    rules = RulesAgent()
    narrator = NarratorAgent()
    
    # Register agents
    agent_mgr.register_agent(story)
    agent_mgr.register_agent(rules)
    agent_mgr.register_agent(narrator)
    
    # Start game processing
    agent_mgr.start()
    ```

=== "Using WebSocket"
    ```python
    from fastapi import FastAPI, WebSocket
    from casys_rpg.api.routes.ws import GameWSConnectionManager
    
    app = FastAPI()
    ws_manager = GameWSConnectionManager()
    
    @app.websocket("/ws/game")
    async def game_websocket(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                # Process game actions
                response = await process_game_action(data)
                await websocket.send_json(response)
        except Exception as e:
            ws_manager.disconnect(websocket)
    ```

## Support

!!! question "Need Help?"
    * Check our [FAQ](../faq/index.md)
    * Join our [Discord](https://discord.gg/casys-rpg)
    * Open an [Issue](https://github.com/yourusername/casys-rpg/issues)
