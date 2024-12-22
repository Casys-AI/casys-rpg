# Installation Guide

This guide will help you set up Casys RPG on your system.

## Prerequisites

Before installing Casys RPG, ensure you have:

- Python 3.8 or higher
- pip (Python package manager)
- OpenAI API key
- Git (for cloning the repository)

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Casys-AI/casys-rpg.git
cd casys-rpg
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment:

=== "Windows"
    ```bash
    .venv\Scripts\activate
    ```

=== "Linux/MacOS"
    ```bash
    source .venv/bin/activate
    ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

### 5. Verify Installation

Run the tests to ensure everything is working:

```bash
pytest
```

## Next Steps

- Follow our [Quick Start Guide](quick-start.md) to begin using Casys RPG
- Read the [Architecture Overview](../architecture/overview.md) to understand the system
- Check out the [API Documentation](../api/overview.md) for detailed reference

## Troubleshooting

If you encounter any issues during installation:

1. Ensure all prerequisites are properly installed
2. Check that your Python version is 3.8 or higher
3. Verify that your OpenAI API key is valid
4. Make sure all environment variables are properly set

For more help, please [open an issue](https://github.com/Casys-AI/casys-rpg/issues) on our GitHub repository.
