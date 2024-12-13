# 🎲 Casys RPG - Interactive Game Book Engine

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28.0-FF4B4B.svg)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-00A36C.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/Casys-AI/casys-rpg/graphs/commit-activity)

<div align="center">

🎮 A modern AI-powered engine for interactive game books, leveraging LLM agents for intelligent rule management and decision-making.

[Features](#features) •
[Quick Start](#quick-start) •
[Architecture](#architecture) •
[Documentation](#documentation) •
[Contributing](#contributing)

</div>

---

## ✨ Features

- 🤖 **Intelligent Agents**: Four specialized LLM agents handling different aspects of the game
- 📚 **RAG-based Rules**: Semantic search and analysis of game rules using FAISS
- 🎲 **Dynamic Dice System**: Context-aware dice rolling system for combat and chance events
- 📊 **Character Stats**: Real-time character statistics tracking
- 🔄 **Game State Management**: Robust state management with save/load capabilities
- 📝 **Feedback System**: Integrated user feedback collection
- 🐛 **Debug Mode**: Built-in debugging tools for development

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/Casys-AI/casys-rpg.git
cd casys-rpg

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Running the Game

```bash
streamlit run app.py
```

## 🏗 Architecture

The system utilizes four specialized LangChain agents:

### 1. RulesAgent 📋
- Implements RAG (Retrieval Augmented Generation) for rule analysis
- FAISS indexing for semantic rule search
- Determines dice roll requirements and types
- Returns structured analysis:
  ```json
  {
    "needs_dice_roll": true|false,
    "dice_type": "chance"|"combat"|null,
    "conditions": ["condition1", "condition2"],
    "next_sections": [1, 2, 3],
    "rules_summary": "Rules summary"
  }
  ```

### 2. DecisionAgent 🤔
- Interprets user responses
- Processes RulesAgent analysis
- Manages dice roll button display
- Validates section choices
- Focuses on decision logic

### 3. NarratorAgent 📖
- Reads book sections
- Formats text for display
- Manages content presentation

### 4. TraceAgent 📝
- Records decisions with context
- Maintains game history
- Enables game state recovery
- Stores character statistics

## 🧩 Core Components

### 1. Application (app.py)
- Streamlit UI interface
- Session state management
- Character statistics display
- Interactive game controls:
  - Dynamic dice roll button
  - Feedback system
  - Debug mode
- Integrated feedback form

### 2. Game Logic (game_logic.py)
- GameState class management
- Agent coordination
- Error handling and logging
- StoryGraph interface

### 3. Utilities (utils/game_utils.py)
- Dice rolling functions
- Data manipulation tools
- Common helper functions

### 4. Agents (agents/)
- story_graph.py: Agent coordination and flow management
- trace_agent.py: History and statistics
- rules_agent.py: Rule analysis
- decision_agent.py: Decision logic
- narrator_agent.py: Content presentation

## 🔄 Game Flow

```mermaid
graph TD
    A[Current Section] --> B[RulesAgent Analysis]
    B --> C[Display Section]
    C --> D[User Response]
    D --> E[DecisionAgent Processing]
    E --> F[TraceAgent Recording]
    F --> G[Stats Update]
    G --> A
```

## 📁 Project Structure

```
.
├── agents/
│   ├── rules_agent.py     # RAG + Rule analysis
│   ├── decision_agent.py  # Decision logic
│   ├── narrator_agent.py  # Content reading
│   ├── trace_agent.py     # History & stats
│   └── story_graph.py     # Coordination
├── utils/
│   └── game_utils.py      # Common utilities
├── data/
│   ├── sections/          # Book text
│   ├── rules/            # Section rules
│   ├── trace/            # Game history
│   └── feedback/         # User feedback
├── app.py                # Streamlit interface
├── game_logic.py         # Core logic
└── requirements.txt      # Dependencies
```

## 📚 Documentation

### LLM Models
- Using `gpt-4o-mini` for all agents
- Temperature settings:
  - RulesAgent: 0 (deterministic)
  - DecisionAgent: 0.7 (controlled creativity)

### Vector Index
- FAISS with L2 metric
- Dimension: 1536 (OpenAI embeddings)
- Updates: On each launch

### Rule Format
- Markdown files
- One file per section: `section_X_rule.md`
- Structure:
  ```markdown
  # Section X Rules
  - Conditions: [...]
  - Possible actions: [...]
  - Next sections: [...]
  ```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Streamlit team for the amazing framework
- LangChain community for the agent framework

---

<div align="center">
Made with ❤️ by Casys AI Team
</div>
