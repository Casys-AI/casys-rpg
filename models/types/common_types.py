"""Common types used across models."""
from enum import Enum

class DiceType(str, Enum):
    """Type of dice roll."""
    NONE = "none"
    CHANCE = "chance"
    COMBAT = "combat"

class NextActionType(str, Enum):
    """Type of next action required."""
    USER_FIRST = "user_first"
    DICE_FIRST = "dice_first"
