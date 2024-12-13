from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import json

class RulesAgent:
    """
    Agent responsable de l'analyse des règles et de la préparation du contexte
    pour l'agent de décision. Il analyse en parallèle de l'affichage du texte
    et prépare les informations nécessaires pour la prise de décision.
    """
    
    def __init__(self, rules_dir: str = "data/rules"):
        """
        Initialise l'agent avec le modèle de langage.
        
        Args:
            rules_dir: Chemin vers le dossier contenant les règles
        """
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.rules_dir = rules_dir
        
    def get_rules_content(self, section_number: int) -> str:
        """Lit le contenu des règles pour une section donnée."""
        rules_file = os.path.join(self.rules_dir, f"section_{section_number}_rule.md")
        if not os.path.exists(rules_file):
            return ""
            
        with open(rules_file, "r", encoding="utf-8") as f:
            return f.read()

    def prepare_context(self, section_number: int) -> dict:
        """
        Analyse les règles d'une section et prépare le contexte pour l'agent de décision.
        Cette méthode est appelée en parallèle de l'affichage du texte.
        
        Args:
            section_number: Numéro de la section à analyser
            
        Returns:
            dict: Contexte pour l'agent de décision avec :
                - needs_dice_roll: bool
                - dice_type: str ou None
                - dice_rules: dict ou None
                - possible_sections: list[int]
                - conditions: list[str]
        """
        current_rules = self.get_rules_content(section_number)
        
        if not current_rules:
            return {
                "needs_dice_roll": False,
                "dice_type": None,
                "dice_rules": None,
                "possible_sections": [],
                "conditions": [],
                "error": "Aucune règle trouvée"
            }

        try:
            # Message système pour expliquer le rôle
            system_message = SystemMessage(content="""Analyse le texte fourni pour préparer le contexte de décision.
            Détermine :
            1. Si un test est nécessaire
            2. Les sections possibles
            3. Les conditions pour chaque section
            
            Format JSON attendu :
            {
                "needs_dice_roll": false,
                "dice_type": null,
                "dice_rules": null,
                "possible_sections": [X, Y],
                "conditions": ["Condition pour X", "Condition pour Y"]
            }""")

            # Message humain avec le texte à analyser
            human_message = HumanMessage(content=f"""Texte à analyser :
{current_rules}

Retourne uniquement le contexte au format JSON spécifié.""")

            # Obtenir l'analyse
            response = self.llm.invoke([system_message, human_message])
            return json.loads(response.content)
            
        except Exception as e:
            print(f"Erreur lors de la préparation du contexte: {str(e)}")
            return {
                "needs_dice_roll": False,
                "dice_type": None,
                "dice_rules": None,
                "possible_sections": [],
                "conditions": [],
                "error": str(e)
            }
