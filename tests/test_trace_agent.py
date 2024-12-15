import pytest
import pytest_asyncio
from agents.trace_agent import TraceAgent
from event_bus import Event, EventBus
from pathlib import Path
import json
import os
from langchain_openai import ChatOpenAI

@pytest_asyncio.fixture
async def event_bus():
    return EventBus()

@pytest_asyncio.fixture
async def trace_agent(event_bus, tmp_path):
    """Fixture qui crée un TraceAgent avec un répertoire temporaire"""
    agent = TraceAgent(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        event_bus=event_bus
    )
    agent.trace_dir = str(tmp_path / "trace")
    return agent

@pytest.mark.asyncio
async def test_record_decision(trace_agent):
    """Test l'enregistrement d'une décision"""
    input_data = {
        "state": {
            "section_number": 1,
            "decision": {
                "next_section": 2,
                "awaiting_action": True,
                "conditions": ["needs_dice_roll"],
                "rules_summary": "Un jet de dé est nécessaire"
            },
            "rules": {
                "needs_dice": True,
                "dice_type": "combat"
            },
            "user_response": "Je vais à gauche"
        }
    }
    
    result = await trace_agent.invoke(input_data)
    
    # Vérifier la structure de base
    assert len(result["history"]) == 1
    entry = result["history"][0]
    
    # Vérifier les champs obligatoires
    assert "timestamp" in entry
    assert entry["section"] == 1
    assert entry["action_type"] == "decision"
    
    # Vérifier les détails de la décision
    assert entry["next_section"] == 2
    assert entry["awaiting_action"] is True
    assert "needs_dice_roll" in entry["conditions"]
    assert entry["rules_summary"] == "Un jet de dé est nécessaire"
    assert entry["user_response"] == "Je vais à gauche"
    
    # Vérifier que le fichier history.json existe et contient les bonnes données
    history_file = Path(trace_agent.session_dir) / "history.json"
    assert history_file.exists()
    with open(history_file, "r", encoding="utf-8") as f:
        saved_history = json.load(f)
    assert len(saved_history) == 1
    assert saved_history[0]["section"] == 1
    assert saved_history[0]["action_type"] == "decision"

@pytest.mark.asyncio
async def test_record_dice_roll(trace_agent):
    """Test l'enregistrement d'un jet de dés."""
    # Préparer les données de test
    test_data = {
        "state": {
            "section_number": 1,
            "dice_result": {
                "type": "combat",
                "value": 6,
                "success": True
            }
        }
    }
    
    # Appeler l'agent
    result = await trace_agent.invoke(test_data)
    
    # Vérifier le résultat
    assert "state" in result
    assert "history" in result["state"]
    assert len(result["state"]["history"]) == 1
    assert result["state"]["history"][0]["action_type"] == "dice_roll"
    assert result["state"]["history"][0]["dice_result"]["value"] == 6

@pytest.mark.asyncio
async def test_multiple_actions_sequence(trace_agent):
    """Test une séquence complète d'actions"""
    # 1. Décision initiale
    await trace_agent.invoke({
        "state": {
            "section_number": 1,
            "decision": {
                "next_section": None,
                "awaiting_action": True,
                "conditions": ["needs_user_input"],
                "rules_summary": "Attente de la décision du joueur"
            }
        }
    })
    
    # 2. Réponse utilisateur
    await trace_agent.invoke({
        "state": {
            "section_number": 1,
            "user_response": "Je vais à gauche",
            "decision": {
                "next_section": None,
                "awaiting_action": True,
                "conditions": ["needs_dice_roll"],
                "rules_summary": "Un jet de dé est nécessaire"
            }
        }
    })
    
    # 3. Lancer de dés
    result = await trace_agent.invoke({
        "state": {
            "section_number": 1,
            "dice_result": {"value": 6, "type": "combat"},
            "decision": {
                "next_section": 2,
                "awaiting_action": False,
                "conditions": ["dice_roll_success"],
                "rules_summary": "Le jet de dé détermine la suite"
            }
        }
    })
    
    # Vérifier la séquence complète
    history = result["history"]
    assert len(history) == 3
    
    # Vérifier la progression des actions
    assert history[0]["action_type"] == "decision"
    assert history[1]["action_type"] == "user_input"
    assert history[2]["action_type"] == "dice_roll"
    
    # Vérifier la cohérence des sections
    assert all(entry["section"] == 1 for entry in history)
    assert history[2]["next_section"] == 2
    
    # Vérifier le fichier
    history_file = Path(trace_agent.session_dir) / "history.json"
    with open(history_file, "r", encoding="utf-8") as f:
        saved_history = json.load(f)
    assert len(saved_history) == 3

@pytest.mark.asyncio
async def test_update_stats(trace_agent):
    """Test la mise à jour des stats"""
    # Stats initiales
    initial_stats = {
        "Caractéristiques": {
            "Habileté": 10,
            "Endurance": 20
        }
    }
    trace_agent.stats = initial_stats
    
    # Mise à jour
    updates = {
        "Caractéristiques": {
            "Habileté": 12
        }
    }
    await trace_agent.update_stats(updates)
    
    # Vérifier les stats en mémoire
    assert trace_agent.stats["Caractéristiques"]["Habileté"] == 12
    assert trace_agent.stats["Caractéristiques"]["Endurance"] == 20  # Inchangé
    
    # Vérifier la sauvegarde
    stats_file = trace_agent.session_dir / "adventure_stats.json"
    assert stats_file.exists()
    with open(stats_file, "r", encoding="utf-8") as f:
        saved_stats = json.load(f)
    assert saved_stats["Caractéristiques"]["Habileté"] == 12

@pytest.mark.asyncio
async def test_stats_persistence(trace_agent):
    """Test la persistance des stats"""
    # Stats initiales
    initial_stats = {
        "Caractéristiques": {
            "Habileté": 10,
            "Endurance": 20
        }
    }
    trace_agent.stats = initial_stats
    await trace_agent.update_stats({})  # Forcer la sauvegarde
    
    # Vérifier le fichier
    stats_file = Path(trace_agent.session_dir) / "adventure_stats.json"
    with open(stats_file, "r", encoding="utf-8") as f:
        saved_stats = json.load(f)
    assert saved_stats == initial_stats

@pytest.mark.asyncio
async def test_adventure_stats_initialization(trace_agent):
    """Test l'initialisation des stats de l'aventure"""
    # Vérifier que le fichier adventure_stats.json est créé
    stats_file = Path(trace_agent.session_dir) / "adventure_stats.json"
    assert stats_file.exists()
    
    # Vérifier le contenu initial
    with open(stats_file, "r", encoding="utf-8") as f:
        stats = json.load(f)
    assert stats == trace_agent.stats

@pytest.mark.asyncio
async def test_update_stats_recursive(trace_agent):
    """Test la mise à jour récursive des stats"""
    # Stats initiales
    initial_stats = {
        "Caractéristiques": {
            "Habileté": 10,
            "Endurance": 20
        },
        "Équipement": {
            "Armes": ["Épée"]
        }
    }
    trace_agent.stats = initial_stats
    
    # Mise à jour partielle
    updates = {
        "Caractéristiques": {
            "Habileté": 12  # Seule l'habileté change
        },
        "Équipement": {
            "Armes": ["Épée", "Dague"]  # Ajout d'une arme
        }
    }
    
    await trace_agent.update_stats(updates)
    
    # Vérifier les mises à jour
    assert trace_agent.stats["Caractéristiques"]["Habileté"] == 12
    assert trace_agent.stats["Caractéristiques"]["Endurance"] == 20  # Inchangé
    assert len(trace_agent.stats["Équipement"]["Armes"]) == 2
    
    # Vérifier la sauvegarde
    stats_file = Path(trace_agent.session_dir) / "adventure_stats.json"
    with open(stats_file, "r", encoding="utf-8") as f:
        saved_stats = json.load(f)
    assert saved_stats == trace_agent.stats

@pytest.mark.asyncio
async def test_get_stats(trace_agent):
    """Test la récupération des stats"""
    # Définir des stats initiales
    initial_stats = {
        "Caractéristiques": {
            "Habileté": 10,
            "Endurance": 20
        }
    }
    trace_agent.stats = initial_stats
    await trace_agent.update_stats({})  # Forcer la sauvegarde
    
    # Récupérer les stats
    stats = trace_agent.get_stats()
    
    # Vérifier que ce sont les bonnes stats
    assert stats == initial_stats
    
    # Modifier les stats en mémoire
    trace_agent.stats["Caractéristiques"]["Habileté"] = 15
    
    # Vérifier que get_stats retourne toujours les stats sauvegardées
    stats = trace_agent.get_stats()
    assert stats["Caractéristiques"]["Habileté"] == 10

@pytest.mark.asyncio
async def test_stats_event_emission(trace_agent):
    """Test l'émission d'événements lors des mises à jour de stats"""
    updates = {
        "Caractéristiques": {
            "Habileté": 12
        }
    }
    
    # Effectuer la mise à jour
    await trace_agent.update_stats(updates)
    
    # Vérifier l'émission de l'événement
    events = trace_agent.event_bus.get_history()
    stats_events = [e for e in events if e.type == "stats_updated"]
    
    assert len(stats_events) > 0
    last_event = stats_events[-1]
    assert "stats" in last_event.data
    assert last_event.data["stats"]["Caractéristiques"]["Habileté"] == 12
