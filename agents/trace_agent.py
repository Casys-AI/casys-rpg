import os
import json
from datetime import datetime
import logging
from typing import Dict

class TraceAgent:
    """
    Agent de traçage pour enregistrer l'état du jeu, les décisions et l'historique.
    """
    def __init__(self, base_dir: str = "data/trace"):
        self.logger = logging.getLogger('TraceAgent')
        self.logger.info("Initialisation du TraceAgent")
        
        self.base_dir = base_dir
        self.current_game_dir = None
        self.state_file = None
        self.initialize_game_session()

    def initialize_game_session(self):
        """
        Initialise une nouvelle session avec un répertoire unique.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        self.current_game_dir = os.path.join(self.base_dir, f"game_{timestamp}")
        os.makedirs(self.current_game_dir, exist_ok=True)
        self.logger.info(f"Nouvelle session créée: {self.current_game_dir}")
        
        self.state_file = os.path.join(self.current_game_dir, "game_state.json")
        self._save_state({
            "current_section": 1,
            "history": []
        })
        self.logger.debug("État initial sauvegardé")

        # Création du fichier des statistiques du personnage
        character_stats_file = os.path.join(self.current_game_dir, "character_stats.md")
        with open(character_stats_file, 'w', encoding='utf-8') as f:
            f.write("""# Statistiques du Personnage

## Caractéristiques
  - Endurance : 20
  - Chance : 20 
  - Habileté : 20 

## Ressources
  - Argent : 2000

## Inventaire
### Objets :
  - """)
        self.logger.info("Statistiques initiales du personnage créées")

    def _save_state(self, state: dict):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        self.logger.debug("État du jeu sauvegardé")

    def _load_state(self) -> dict:
        if not os.path.exists(self.state_file):
            return {"current_section": 1, "history": []}
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_current_section(self) -> int:
        state = self._load_state()
        return state.get("current_section", 1)

    def record_decision(self, section_number: int, user_response: str, next_section: int, context: Dict = None, dice_result: int = None) -> str:
        """
        Enregistre la décision et met à jour l'état du jeu.
        """
        self.logger.info(f"Enregistrement décision: Section {section_number} -> {next_section}")
        self.logger.debug(f"Réponse utilisateur: '{user_response}'")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        trace_file = os.path.join(self.current_game_dir, f"section_{section_number}_{timestamp}.md")

        try:
            content = f"""# Trace de la section {section_number}
Timestamp: {timestamp}

## Réponse de l'utilisateur
{user_response}

## Décision
Section suivante: {next_section}
"""
            if dice_result is not None:
                content += f"\nRésultat du dé: {dice_result}"
                
            content += "\n---\n"
            
            with open(trace_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.debug(f"Trace sauvegardée: {trace_file}")
            
            state = self._load_state()
            state["current_section"] = next_section
            state["history"].append({
                "timestamp": timestamp,
                "section": section_number,
                "response": user_response,
                "next_section": next_section,
                "dice_result": dice_result
            })
            self._save_state(state)
            
            return trace_file
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de la trace: {str(e)}")
            return ""

    def get_current_game_dir(self) -> str:
        return self.current_game_dir

    def get_last_state(self) -> dict:
        """Récupère le dernier état enregistré."""
        state = self._load_state()
        if not state["history"]:
            return None
            
        last_decision = state["history"][-1]
        return {
            "current_section": last_decision["section"],
            "user_response": last_decision["response"],
            "next_section": last_decision["next_section"],
            "timestamp": last_decision.get("timestamp", "Unknown")
        }

    def get_character_stats(self) -> Dict:
        """
        Récupère les statistiques du personnage depuis le fichier de trace.
        
        Returns:
            Dict contenant les stats du personnage
        """
        try:
            stats_file = os.path.join(self.current_game_dir, "character_stats.md")
            if not os.path.exists(stats_file):
                return self._init_character_stats()
                
            with open(stats_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parser le contenu markdown en dictionnaire
            stats = {
                "Caractéristiques": {},
                "Ressources": {},
                "Inventaire": {"Objets": []}
            }
            
            current_section = None
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('###'):
                    current_section = line[4:].strip()
                elif line and current_section:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if current_section == "Caractéristiques":
                            try:
                                stats["Caractéristiques"][key] = int(value)
                            except ValueError:
                                stats["Caractéristiques"][key] = value
                        elif current_section == "Ressources":
                            try:
                                stats["Ressources"][key] = int(value)
                            except ValueError:
                                stats["Ressources"][key] = value
                    elif current_section == "Inventaire" and line.startswith('-'):
                        item = line[1:].strip()
                        if item:
                            stats["Inventaire"]["Objets"].append(item)
                            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture des stats: {str(e)}")
            return self._init_character_stats()
            
    def _init_character_stats(self) -> Dict:
        """
        Initialise les statistiques par défaut du personnage.
        
        Returns:
            Dict avec les stats par défaut
        """
        return {
            "Caractéristiques": {
                "Habileté": 0,
                "Endurance": 0,
                "Chance": 0
            },
            "Ressources": {},
            "Inventaire": {"Objets": []}
        }

    def update_character_stats(self, stats_updates: dict):
        """
        Met à jour les statistiques du personnage.
        """
        self.logger.info("Mise à jour des statistiques du personnage")
        stats_file = os.path.join(self.current_game_dir, "character_stats.md")
        current_stats = self.get_character_stats()
        
        # Mettre à jour les stats
        for category, values in stats_updates.items():
            if category not in current_stats:
                current_stats[category] = {}
            current_stats[category].update(values)
        
        # Générer le nouveau contenu
        content = "# Statistiques du Personnage\n\n"
        
        if "Caractéristiques" in current_stats:
            content += "## Caractéristiques\n"
            for stat, value in current_stats["Caractéristiques"].items():
                content += f"  - {stat} : {value}\n"
            content += "\n"
        
        if "Ressources" in current_stats:
            content += "## Ressources\n"
            for resource, value in current_stats["Ressources"].items():
                content += f"  - {resource} : {value}\n"
            content += "\n"
        
        if "Inventaire" in current_stats:
            content += "## Inventaire\n### Objets :\n"
            for item in current_stats["Inventaire"].get("Objets", []):
                content += f"  - {item}\n"
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(content)
        self.logger.debug("Statistiques du personnage mises à jour")

    def _parse_stats(self, content: str) -> dict:
        """
        Parse le contenu du fichier de stats en dictionnaire.
        """
        stats = {
            "Caractéristiques": {},
            "Ressources": {},
            "Inventaire": {"Objets": []}
        }
        
        current_section = None
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('## '):
                current_section = line[3:]
                continue
                
            if line.startswith('### '):
                continue
                
            if line.startswith('  - '):
                item = line[4:]
                if current_section in ["Caractéristiques", "Ressources"]:
                    if ':' in item:
                        key, value = item.split(' : ')
                        stats[current_section][key] = int(value)
                elif current_section == "Inventaire" and item:
                    stats["Inventaire"]["Objets"].append(item)
        
        return stats
