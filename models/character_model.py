"""Models for character management."""
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

class CharacterStats(BaseModel):
    """Character's base statistics."""
    endurance: int = Field(default=20, description="Character's endurance")
    chance: int = Field(default=20, description="Character's luck")
    skill: int = Field(default=20, description="Character's combat skill")
    
    @field_validator('endurance', 'chance', 'skill')
    def validate_positive_stats(cls, v):
        if v < 0:
            raise ValueError("Stats must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_stats_range(self):
        """Validate that stats are within acceptable ranges."""
        if self.endurance > 24:
            raise ValueError("Endurance cannot exceed 24")
        if self.chance > 24:
            raise ValueError("Chance cannot exceed 24")
        if self.skill > 24:
            raise ValueError("Skill cannot exceed 24")
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
    capacity: int = Field(default=10, ge=0)
    gold: int = Field(default=0, ge=0)
    
    @model_validator(mode='after')
    def validate_capacity(self):
        """Validate inventory capacity."""
        total_items = sum(item.quantity for item in self.items.values())
        if total_items > self.capacity:
            raise ValueError(f"Total items ({total_items}) exceeds capacity ({self.capacity})")
        return self
    
    @field_validator('gold')
    def validate_gold(cls, v):
        """Validate gold amount."""
        if v < 0:
            raise ValueError("Gold cannot be negative")
        if v > 999999:
            raise ValueError("Gold amount exceeds maximum allowed (999999)")
        return v

class CharacterModel(BaseModel):
    """Current state of the character."""
    name: str = Field(default="Hero", description="Character's name")
    stats: CharacterStats = Field(default_factory=CharacterStats)
    inventory: Inventory = Field(default_factory=Inventory)
    
    @field_validator('name')
    def validate_name(cls, v):
        """Validate character name."""
        if not v.strip():
            raise ValueError("Character name cannot be empty")
        if len(v) > 50:
            raise ValueError("Character name too long (max 50 characters)")
        return v
    
    def update_stats(self, new_stats: Dict[str, Any]):
        """Update character stats."""
        self.stats = self.stats.model_copy(update=new_stats)
        
    def add_item(self, item: Item):
        """Add item to inventory if capacity allows."""
        if item.name in self.inventory.items:
            # Update existing item quantity
            existing_item = self.inventory.items[item.name]
            total_quantity = existing_item.quantity + item.quantity
            self.inventory.items[item.name] = existing_item.model_copy(update={"quantity": total_quantity})
        else:
            # Add new item
            self.inventory.items[item.name] = item
            
        # Validate capacity after update
        self.inventory.validate_capacity()
        
    def remove_item(self, item_name: str):
        """Remove item from inventory."""
        if item_name in self.inventory.items:
            del self.inventory.items[item_name]
