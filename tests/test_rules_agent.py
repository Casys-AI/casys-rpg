"""
# 🎲 RulesAgent Test Specifications

## Overview
Test suite for the RulesAgent component of the Casys RPG engine. The RulesAgent is responsible
for analyzing game rules and determining required actions (dice rolls, choices).

## Test Architecture
Each test focuses on a specific aspect of the RulesAgent's functionality, following
the component's role in the game engine architecture.

## Test Categories

### 1. Basic Functionality Test
**Purpose**: Verify basic response format and content validation
**Input Data Format**:
```json
{
    "state": {
        "section_number": 1
    }
}
```
**Expected Output Format**:
```json
{
    "state": {
        "choices": ["list of choices"],
        "needs_dice": boolean,
        "dice_type": "combat"|"chance"|null,
        "rules": "rule text"
    }
}
```

### 2. Cache Mechanism Test
**Purpose**: Verify caching behavior and response consistency
**Cache Structure**:
```python
cache = {
    section_number: "rules_text",
    ...
}
```
**Validation Points**:
- Response consistency across calls
- Cache hit behavior
- Field preservation

### 3. Input Validation Test
**Purpose**: Verify error handling and input validation
**Error Cases**:
- Missing section number
- Invalid section number (negative)
- Malformed input
**Error Format**:
```json
{
    "state": {
        "error": "error message",
        "choices": [],
        "needs_dice": false,
        "dice_type": null
    }
}
```

### 4. Dice Roll Detection Test
**Purpose**: Verify dice roll requirement detection
**Dice Types**:
- Combat: For battle scenarios
- Chance: For luck/skill checks
**Trigger Words**:
- Combat: ["combat", "fight", "battle"]
- Chance: ["chance", "luck", "fortune"]
**Detection Format**:
```json
{
    "state": {
        "needs_dice": true,
        "dice_type": "combat"|"chance",
        "awaiting_action": true
    }
}
```

## Test Dependencies
- pytest-asyncio: For async test execution
- pytest: Test framework
- langchain_community: LLM integration

## Model Configuration
- Model: gpt-4o-mini
- Temperature: 0 (deterministic for rules)
"""

import os
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from langchain.schema import SystemMessage, AIMessage
from agents.rules_agent import RulesAgent, RulesConfig
import asyncio
import tempfile
import shutil
import logging
import sys
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration du logging pour les tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class MockLLM:
    async def ainvoke(self, messages):
        # Log le prompt reçu
        logging.debug(f"[MockLLM] Received prompt: {messages[1].content}")
        
        # Simuler une réponse du LLM
        response = {
            "needs_dice": True,
            "dice_type": "combat",
            "next_sections": [2, 3],
            "conditions": ["Réussir le jet de combat"],
            "choices": ["Combat"],
            "rules_summary": "Un combat nécessitant un jet de dés"
        }
        
        # Log la réponse
        logging.debug(f"[MockLLM] Returning response: {json.dumps(response, indent=2)}")
        
        return AIMessage(content=json.dumps(response))

@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    if not loop.is_closed():
        loop.stop()
        loop.close()
    asyncio.set_event_loop(None)

@pytest.fixture
def rules_agent():
    """Fixture pour le RulesAgent"""
    config = RulesConfig()
    config.llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    return RulesAgent(config=config)

@pytest.fixture
def clean_cache():
    """Nettoie le cache avant et après les tests"""
    cache_dir = os.path.join("data", "rules", "cache")
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
    os.makedirs(cache_dir)
    yield
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)

@pytest.mark.asyncio
async def test_rules_agent_basic(rules_agent):
    """Test basique de l'agent des règles"""
    input_data = {
        "state": {
            "section_number": 1,
            "current_section": {
                "content": "Test content"
            }
        }
    }
    
    async for result in rules_agent.ainvoke(input_data):
        assert "state" in result
        assert "rules" in result["state"]
        assert "needs_dice" in result["state"]["rules"]

@pytest.mark.asyncio
async def test_rules_agent_cache(rules_agent, clean_cache):
    """Test du cache sur disque"""
    input_data = {
        "state": {
            "section_number": 1,
            "current_section": {
                "content": "Test content"
            }
        }
    }
    
    # Premier appel - devrait analyser et mettre en cache
    async for result1 in rules_agent.ainvoke(input_data):
        assert "rules" in result1["state"]
        rules1 = result1["state"]["rules"]
    
    # Deuxième appel - devrait utiliser le cache
    async for result2 in rules_agent.ainvoke(input_data):
        assert "rules" in result2["state"]
        rules2 = result2["state"]["rules"]
        
        # Vérifier que les résultats sont identiques
        assert rules1 == rules2

@pytest.mark.asyncio
async def test_rules_agent_cache_error(rules_agent, clean_cache):
    """Test de la gestion des erreurs de cache"""
    input_data = {
        "state": {
            "section_number": 999,  # Section inexistante
            "current_section": {}  # Pas de contenu
        }
    }
    
    async for result in rules_agent.ainvoke(input_data):
        assert "state" in result
        assert "rules" in result["state"]
        assert "error" in result["state"]["rules"]
        assert "No content found for section 999" in result["state"]["rules"]["error"]

@pytest.mark.asyncio
async def test_rules_agent_dice_handling(rules_agent):
    """Test la détection des jets de dés"""
    test_state = {
        "state": {
            "section_number": 1,
            "current_section": {
                "content": """
                Vous devez faire un jet de dés de combat.
                Si vous réussissez, allez à la section 2.
                """
            }
        }
    }
    
    async for result in rules_agent.ainvoke(test_state):
        assert "rules" in result["state"]
        rules = result["state"]["rules"]
        assert rules["needs_dice"] == True
        assert rules["dice_type"] == "combat"
        assert 2 in rules["next_sections"]

@pytest.mark.asyncio
async def test_rules_agent_invalid_section(rules_agent):
    """Test avec un numéro de section invalide"""
    input_data = {
        "state": {
            "section_number": -1
        }
    }
    
    async for result in rules_agent.ainvoke(input_data):
        assert "state" in result
        assert "rules" in result["state"]
        assert "error" in result["state"]["rules"]
        assert "No content found for section -1" in result["state"]["rules"]["error"]

@pytest.mark.asyncio
async def test_rules_agent_analyze_content(rules_agent):
    """Test de l'analyse de contenu"""
    content = """
    Vous êtes dans une pièce sombre. Vous pouvez:
    - Allumer une torche et aller au [[2]]
    - Continuer dans l'obscurité vers le [[3]]
    """
    
    result = await rules_agent._analyze_rules(1, content)
    assert isinstance(result, dict)
    assert "choices" in result
    assert "next_sections" in result

@pytest.mark.asyncio
async def test_rules_agent_invalid_input(rules_agent):
    """Test la gestion des entrées invalides"""
    async for result in rules_agent.ainvoke({"state": {}}):
        assert "state" in result
        assert "rules" in result["state"]
        assert "error" in result["state"]["rules"]
        assert "No section number provided" in result["state"]["rules"]["error"]

@pytest.mark.asyncio
async def test_rules_agent_state_transmission(rules_agent):
    """Test que les règles sont correctement transmises dans le state"""
    
    async for result in rules_agent.ainvoke({
        "state": {
            "section_number": 1,
            "current_section": {
                "content": """Dans cette section, vous devez faire un jet de dés de combat.
                
Si vous réussissez votre jet de combat, allez à la section 2.
Si vous échouez, allez à la section 3.

Faites votre choix avec sagesse."""
            }
        }
    }):
        # Vérifier la structure du state
        assert "state" in result
        assert "rules" in result["state"]
        
        # Vérifier les champs essentiels des règles
        rules = result["state"]["rules"]
        assert "needs_dice" in rules
        assert "dice_type" in rules
        assert "next_sections" in rules
        assert "conditions" in rules
        assert "choices" in rules
        
        # Vérifier les valeurs spécifiques basées sur le contenu
        assert rules["needs_dice"] == True, "Un jet de dés est requis"
        assert rules["dice_type"] == "combat", "Le type de dé devrait être combat"
        assert 2 in rules["next_sections"], "La section 2 devrait être une destination possible"
        assert 3 in rules["next_sections"], "La section 3 devrait être une destination possible"
        assert len(rules["next_sections"]) == 2, "Il devrait y avoir exactement 2 sections possibles"
