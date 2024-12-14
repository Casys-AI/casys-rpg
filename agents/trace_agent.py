# agents/trace_agent.py
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List
import logging
from event_bus import EventBus, Event
from datetime import datetime
import os
import json
from pathlib import Path

class TraceAgent(RunnableSerializable[Dict, Dict]):
    """
    Agent qui trace les actions et les statistiques du personnage.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    event_bus: EventBus = Field(..., description="Bus d'événements pour la communication")
    history: List[Dict] = Field(default_factory=list)
    stats: Dict = Field(default_factory=lambda: {
        "Caractéristiques": {
            "Habileté": 10,
            "Chance": 5,
            "Endurance": 8
        },
        "Ressources": {
            "Or": 100,
            "Gemme": 5
        },
        "Inventaire": {
            "Objets": ["Épée", "Bouclier"]
        }
    })
    trace_dir: str = Field(default="data/trace")
    session_dir: Path = Field(default_factory=lambda: Path("data/trace"))
    
    def __init__(self, **data):
        super().__init__(**data)
        self.trace_dir = Path(self.trace_dir)  # Convertir en Path
        self.session_dir = self.create_session_dir()
        self.save_adventure_stats()
    
    def create_session_dir(self) -> Path:
        """Crée le répertoire de session pour cette partie"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.trace_dir / f"game_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def save_adventure_stats(self) -> None:
        """Sauvegarde les statistiques de l'aventure"""
        stats_file = self.session_dir / "adventure_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    async def invoke(self, input_data: Dict) -> Dict:
        """
        Enregistre une action dans l'historique.
        
        Args:
            input_data (Dict): Données de l'action
            
        Returns:
            Dict: État mis à jour
        """
        try:
            # Déterminer le type d'action
            action_type = "unknown"
            
            # Si on a un résultat de dés et que needs_dice est True
            if "dice_result" in input_data and input_data.get("rules", {}).get("needs_dice", False):
                action_type = "dice_roll"
            # Si on a une décision
            elif "decision" in input_data:
                # Si on a une réponse utilisateur mais pas de next_section
                # c'est une réponse utilisateur
                if "user_response" in input_data and not input_data["decision"].get("next_section"):
                    action_type = "user_input"
                else:
                    action_type = "decision"
            # Si on a juste une réponse utilisateur
            elif "user_response" in input_data:
                action_type = "user_input"

            # Créer l'entrée d'historique
            entry = {
                "timestamp": datetime.now().isoformat(),
                "section": input_data.get("section_number"),
                "action_type": action_type
            }

            # Ajouter les détails spécifiques selon le type d'action
            if action_type == "dice_roll":
                entry.update({
                    "dice_result": input_data["dice_result"],
                    "dice_type": input_data["dice_result"].get("type", "normal")
                })
            
            # Toujours inclure la réponse utilisateur si elle existe
            if "user_response" in input_data:
                entry["user_response"] = input_data["user_response"]
            
            # Ajouter les détails de la décision si présente
            if "decision" in input_data:
                entry.update(input_data["decision"])

            # Ajouter à l'historique
            self.history.append(entry)
            
            # Sauvegarder l'historique
            history_file = self.session_dir / "history.json"
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            
            # Émettre un événement
            await self.event_bus.emit(Event(
                type="trace_updated",
                data={
                    "history": self.history,
                    "stats": self.get_stats()
                }
            ))
            
            return {
                "history": self.history,
                "stats": self.get_stats()
            }

        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement : {str(e)}")
            return {
                "error": str(e),
                "history": self.history,
                "stats": self.get_stats()
            }

    async def update_stats(self, updates: Dict) -> None:
        """
        Met à jour les statistiques du personnage.
        
        Args:
            updates (Dict): Nouvelles statistiques à appliquer
        """
        # Mise à jour récursive des stats
        self._recursive_update(self.stats, updates)
        
        # Sauvegarder les stats mises à jour
        stats_file = self.session_dir / "adventure_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        # Émettre un événement de mise à jour
        await self.event_bus.emit(Event(
            type="stats_updated",
            data={"stats": self.stats}
        ))

    def _recursive_update(self, current: Dict, updates: Dict) -> None:
        """
        Met à jour récursivement un dictionnaire.
        
        Args:
            current (Dict): Dictionnaire actuel
            updates (Dict): Mises à jour à appliquer
        """
        for key, value in updates.items():
            if key in current and isinstance(current[key], dict) and isinstance(value, dict):
                self._recursive_update(current[key], value)
            else:
                current[key] = value

    def get_stats(self) -> Dict:
        """
        Récupère les statistiques actuelles.
        
        Returns:
            Dict: Statistiques du personnage
        """
        stats_file = self.session_dir / "adventure_stats.json"
        if stats_file.exists():
            with open(stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return self.stats
    
    def get_history(self) -> List[Dict]:
        """
        Récupère l'historique des actions.
        
        Returns:
            List[Dict]: Historique des actions
        """
        return self.history.copy()
