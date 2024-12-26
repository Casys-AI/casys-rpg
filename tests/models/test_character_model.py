"""Tests for character model."""
import pytest
from models.character_model import CharacterModel, CharacterStats, Item, Inventory

def test_character_stats_creation():
    """Test creation of character stats with default values."""
    stats = CharacterStats()
    assert stats.health == 100
    assert stats.max_health == 100
    assert stats.strength == 10
    assert stats.dexterity == 10
    assert stats.intelligence == 10
    assert stats.level == 1
    assert stats.experience == 0

def test_character_stats_validation():
    """Test validation of character stats."""
    with pytest.raises(ValueError):
        CharacterStats(health=-1)
    
    with pytest.raises(ValueError):
        CharacterStats(strength=-5)
    
    stats = CharacterStats(health=150, max_health=100)
    assert stats.health == 100  # Should be capped at max_health

def test_item_creation():
    """Test creation and validation of items."""
    item = Item(name="Potion", quantity=2)
    assert item.name == "Potion"
    assert item.quantity == 2
    
    with pytest.raises(ValueError):
        Item(name="", quantity=1)
    
    with pytest.raises(ValueError):
        Item(name="Potion", quantity=-1)

def test_inventory_management():
    """Test inventory capacity and item management."""
    inventory = Inventory(capacity=2)
    inventory.items["Potion"] = Item(name="Potion")
    inventory.items["Sword"] = Item(name="Sword")
    assert len(inventory.items) == 2
    
    # Tenter d'ajouter un item quand l'inventaire est plein
    inventory.items["Shield"] = Item(name="Shield")
    with pytest.raises(ValueError):
        # La validation se fait lors de la création d'un nouveau modèle
        Inventory(items=inventory.items, capacity=2)

def test_character_model_integration():
    """Test full character model functionality."""
    character = CharacterModel()
    
    character.update_stats({"health": 80, "strength": 15})
    assert character.stats.health == 80
    assert character.stats.strength == 15
    
    item = Item(name="Potion", quantity=1)
    character.add_item(item)
    assert "Potion" in character.inventory.items
    
    character.remove_item("Potion")
    assert "Potion" not in character.inventory.items

def test_inventory_gold_management():
    """Test gold handling in inventory."""
    inventory = Inventory(gold=100)
    assert inventory.gold == 100
    
    with pytest.raises(ValueError):
        Inventory(gold=-10)

def test_character_model_full_inventory():
    """Test behavior when inventory is full."""
    character = CharacterModel(inventory=Inventory(capacity=1))
    character.add_item(Item(name="Sword"))
    
    with pytest.raises(ValueError):
        character.add_item(Item(name="Shield"))

def test_character_stats_experience_system():
    """Test experience and leveling system."""
    stats = CharacterStats(experience=100)
    assert stats.experience == 100
    assert stats.level == 1
    
    with pytest.raises(ValueError):
        CharacterStats(experience=-10)
