import random

def roll_dice() -> int:
    """
    Effectue un lancer de 2d6 (deux dés à 6 faces).
    
    Returns:
        int: valeur du lancer
    """
    # Lancer 2d6
    dice_value = random.randint(1, 6) + random.randint(1, 6)
    
    # Note : La comparaison avec le score de chance est faite par l'agent de décision
    # car elle dépend des règles qui peuvent changer
    return dice_value
