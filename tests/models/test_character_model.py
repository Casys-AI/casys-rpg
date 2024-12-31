"""Tests for character model."""
import pytest
from datetime import datetime
from copy import deepcopy

from models.character_model import CharacterModel, CharacterStats, Item, Inventory
from models.errors_model import CharacterError

@pytest.fixture
def sample_character_model():
    return CharacterModel(name="Test Character", stats=CharacterStats(endurance=20, chance=20, skill=20))

@pytest.fixture
def model_factory():
    class ModelFactory:
        def create_character(self, name="Test Character", stats=None, inventory=None):
            if stats is None:
                stats = CharacterStats(endurance=20, chance=20, skill=20)
            if inventory is None:
                inventory = Inventory(capacity=10)
            return CharacterModel(name=name, stats=stats, inventory=inventory)

        def create_character_stats(self, endurance=20, chance=20, skill=20):
            return CharacterStats(endurance=endurance, chance=chance, skill=skill)

        def create_item(self, name="Potion", quantity=1, description=""):
            return Item(name=name, quantity=quantity, description=description)

        def create_inventory(self, capacity=10, gold=0):
            return Inventory(capacity=capacity, gold=gold)

    return ModelFactory()

def test_character_model_creation(sample_character_model: CharacterModel):
    """Test creation of character model with default values."""
    assert sample_character_model.name == "Test Character"
    assert isinstance(sample_character_model.stats, CharacterStats)
    assert isinstance(sample_character_model.inventory, Inventory)
    # Test default stats
    assert sample_character_model.stats.endurance == 20
    assert sample_character_model.stats.chance == 20
    assert sample_character_model.stats.skill == 20

def test_character_stats_validation(model_factory):
    """Test validation of character stats."""
    # Test invalid stats values
    with pytest.raises(ValueError, match="must be greater than 0"):
        model_factory.create_character_stats(endurance=-1)
    
    with pytest.raises(ValueError, match="must be greater than 0"):
        model_factory.create_character_stats(chance=-5)
    
    with pytest.raises(ValueError, match="must be greater than 0"):
        model_factory.create_character_stats(skill=-3)
    
    # Test maximum values
    with pytest.raises(ValueError, match="must be less than or equal to 30"):
        model_factory.create_character_stats(endurance=31)
    
    with pytest.raises(ValueError, match="must be less than or equal to 30"):
        model_factory.create_character_stats(chance=31)
    
    with pytest.raises(ValueError, match="must be less than or equal to 30"):
        model_factory.create_character_stats(skill=31)

def test_item_validation(model_factory):
    """Test validation of items."""
    # Test valid item
    item = model_factory.create_item(
        name="Potion",
        quantity=2,
        description="Healing potion"
    )
    assert item.name == "Potion"
    assert item.quantity == 2
    assert item.description == "Healing potion"
    
    # Test invalid item name
    with pytest.raises(ValueError, match="name cannot be empty"):
        model_factory.create_item(name="")
    
    # Test invalid quantity
    with pytest.raises(ValueError, match="must be greater than 0"):
        model_factory.create_item(quantity=-1)
    
    # Test maximum quantity
    with pytest.raises(ValueError, match="must be less than or equal to"):
        model_factory.create_item(quantity=100)

def test_inventory_management(model_factory):
    """Test inventory capacity and item management."""
    inventory = model_factory.create_inventory(capacity=2)
    
    # Add items
    potion = model_factory.create_item(name="Potion")
    sword = model_factory.create_item(name="Sword")
    
    # Test adding items
    inventory = inventory.add_item(potion)
    inventory = inventory.add_item(sword)
    assert len(inventory.items) == 2
    assert "Potion" in inventory.items
    assert "Sword" in inventory.items
    
    # Test inventory full
    shield = model_factory.create_item(name="Shield")
    with pytest.raises(CharacterError, match="Inventory is full"):
        inventory.add_item(shield)
    
    # Test remove item
    inventory = inventory.remove_item("Potion")
    assert len(inventory.items) == 1
    assert "Potion" not in inventory.items
    assert "Sword" in inventory.items
    
    # Test remove non-existent item
    with pytest.raises(CharacterError, match="Item not found"):
        inventory.remove_item("NonExistentItem")

def test_inventory_gold_management(model_factory):
    """Test gold handling in inventory."""
    inventory = model_factory.create_inventory(gold=10)
    
    # Test adding gold
    inventory = inventory.add_gold(5)
    assert inventory.gold == 15
    
    # Test removing gold
    inventory = inventory.remove_gold(3)
    assert inventory.gold == 12
    
    # Test removing too much gold
    with pytest.raises(ValueError, match="Not enough gold"):
        inventory.remove_gold(20)
    
    # Test negative gold amount
    with pytest.raises(ValueError, match="must be greater than 0"):
        inventory.add_gold(-5)

def test_character_model_immutability(sample_character_model: CharacterModel):
    """Test character model immutability."""
    # Try to modify stats
    new_stats = CharacterStats(endurance=25, chance=15, skill=20)
    updated_model = sample_character_model.model_copy(update={"stats": new_stats})
    
    # Original should be unchanged
    assert sample_character_model.stats.endurance == 20
    assert updated_model.stats.endurance == 25
    
    # Try to modify inventory
    potion = Item(name="Potion", quantity=1)
    updated_model = updated_model.add_item(potion)
    
    # Original should be unchanged
    assert "Potion" not in sample_character_model.inventory.items
    assert "Potion" in updated_model.inventory.items

def test_inventory_item_stacking(model_factory):
    """Test item stacking in inventory."""
    inventory = model_factory.create_inventory()
    
    # Add first potion
    potion1 = model_factory.create_item(name="Potion", quantity=1)
    inventory = inventory.add_item(potion1)
    
    # Add second potion
    potion2 = model_factory.create_item(name="Potion", quantity=2)
    inventory = inventory.add_item(potion2)
    
    # Check stacking
    assert len(inventory.items) == 1
    assert inventory.items["Potion"].quantity == 3
    
    # Test maximum stack size
    potion3 = model_factory.create_item(name="Potion", quantity=98)
    with pytest.raises(ValueError, match="Exceeds maximum stack size"):
        inventory.add_item(potion3)

def test_character_model_serialization(sample_character_model: CharacterModel):
    """Test character model serialization."""
    # Serialize to dict
    char_dict = sample_character_model.model_dump()
    
    # Check basic fields
    assert char_dict["name"] == "Test Character"
    assert isinstance(char_dict["stats"], dict)
    assert isinstance(char_dict["inventory"], dict)
    
    # Check stats
    assert char_dict["stats"]["endurance"] == 20
    assert char_dict["stats"]["chance"] == 20
    assert char_dict["stats"]["skill"] == 20
    
    # Check inventory
    assert isinstance(char_dict["inventory"]["items"], dict)
    assert char_dict["inventory"]["capacity"] == 10
    assert char_dict["inventory"]["gold"] == 0

def test_character_stats_modification(model_factory):
    """Test modification of character stats."""
    char = model_factory.create_character()
    
    # Modify stats
    new_stats = model_factory.create_character_stats(
        endurance=25,
        chance=15,
        skill=18
    )
    updated_char = char.model_copy(update={"stats": new_stats})
    
    # Check updates
    assert updated_char.stats.endurance == 25
    assert updated_char.stats.chance == 15
    assert updated_char.stats.skill == 18
    
    # Original should be unchanged
    assert char.stats.endurance == 20
    assert char.stats.chance == 20
    assert char.stats.skill == 20

def test_character_inventory_operations(model_factory):
    """Test complex inventory operations."""
    char = model_factory.create_character()
    
    # Add multiple items
    sword = model_factory.create_item(name="Sword", quantity=1)
    shield = model_factory.create_item(name="Shield", quantity=1)
    potion = model_factory.create_item(name="Potion", quantity=3)
    
    # Add items sequentially
    char = char.add_item(sword)
    char = char.add_item(shield)
    char = char.add_item(potion)
    
    # Verify inventory state
    assert len(char.inventory.items) == 3
    assert char.inventory.items["Sword"].quantity == 1
    assert char.inventory.items["Shield"].quantity == 1
    assert char.inventory.items["Potion"].quantity == 3
    
    # Remove and re-add items
    char = char.remove_item("Shield")
    assert "Shield" not in char.inventory.items
    
    # Add gold and items
    char = char.add_gold(50)
    new_shield = model_factory.create_item(name="Shield", quantity=1)
    char = char.add_item(new_shield)
    
    # Final state check
    assert char.inventory.gold == 50
    assert "Shield" in char.inventory.items
    assert len(char.inventory.items) == 3
