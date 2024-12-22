"""Models for character management."""
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

class CharacterStats(BaseModel):
    """Character's base statistics."""
    health: int = 100
    max_health: int = 100
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    level: int = 1
    experience: int = 0
    
    @field_validator('health', 'max_health', 'strength', 'dexterity', 'intelligence', 'level', 'experience')
    def validate_positive_stats(cls, v):
        if v < 0:
            raise ValueError("Stats must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_health(self):
        if self.health > self.max_health:
            self.health = self.max_health
        return self

class Item(BaseModel):
    """An item in the character's inventory."""
    name: str
    quantity: int = 1
    description: str = ""
    effects: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Item name cannot be empty")
        return v
    
    @field_validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError("Quantity must be positive")
        return v

class Inventory(BaseModel):
    """Character's inventory."""
    items: Dict[str, Item] = Field(default_factory=dict)
    capacity: int = 10
    gold: int = 0
    
    @field_validator('capacity', 'gold')
    def validate_positive_values(cls, v, field):
        if v < 0:
            raise ValueError(f"{field.name} must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_inventory_size(self):
        if len(self.items) > self.capacity:
            raise ValueError("Inventory is full")
        return self

class CharacterModel(BaseModel):
    """Current state of the character."""
    stats: CharacterStats = Field(default_factory=CharacterStats)
    inventory: Inventory = Field(default_factory=Inventory)
    
    def update_stats(self, new_stats: Dict[str, Any]):
        """Update character stats."""
        for key, value in new_stats.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)
    
    def add_item(self, item: Item):
        """Add item to inventory if capacity allows."""
        if len(self.inventory.items) >= self.inventory.capacity:
            raise ValueError("Inventory is full")
        self.inventory.items[item.name] = item
    
    def remove_item(self, item_name: str):
        """Remove item from inventory."""
        if item_name in self.inventory.items:
            del self.inventory.items[item_name]
