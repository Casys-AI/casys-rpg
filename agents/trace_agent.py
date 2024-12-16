# agents/trace_agent.py
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, AsyncGenerator
import logging
from event_bus import EventBus, Event
from datetime import datetime
import os
import json
from pathlib import Path
import shutil

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
        self.history = []  # Réinitialiser l'historique
        self.save_adventure_stats()
        self.save_history()  # Sauvegarder l'historique initial
    
    def create_session_dir(self) -> Path:
        """Crée le répertoire de session pour cette partie"""
        # Supprimer les anciens dossiers de session si nécessaire
        if self.trace_dir.exists():
            for old_dir in self.trace_dir.glob("game_*"):
                if old_dir.is_dir():
                    shutil.rmtree(old_dir)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.trace_dir / f"game_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def save_adventure_stats(self) -> None:
        """Sauvegarde les statistiques de l'aventure"""
        stats_file = self.session_dir / "adventure_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def save_history(self) -> None:
        """Sauvegarde l'historique des actions"""
        history_file = self.session_dir / "history.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    async def invoke(self, input_data: Dict) -> Dict:
        """
        Enregistre une action dans l'historique et met à jour les stats si nécessaire.
        
        Args:
            input_data (Dict): Données de l'action avec state
            
        Returns:
            Dict: État mis à jour avec historique et stats
        """
        try:
            # Extraire l'état ou initialiser un nouveau
            state = input_data.get("state", {}).copy()
            if not state:
                state = {}
            
            # Déterminer le type d'action
            action_type = "unknown"
            if "dice_result" in state:
                action_type = "dice_roll"
            elif "user_response" in state and (
                "decision" not in state or 
                not state.get("decision", {}).get("next_section")
            ):
                action_type = "user_input"
            elif "decision" in state:
                action_type = "decision"
            elif "user_response" in state:
                action_type = "user_input"

            # Créer l'entrée d'historique
            entry = {
                "timestamp": datetime.now().isoformat(),
                "section": state.get("section_number"),
                "action_type": action_type,
                "stats": self.stats.copy()
            }

            # Ajouter la réponse utilisateur si présente
            if "user_response" in state:
                entry["user_response"] = state["user_response"]

            # Ajouter les détails spécifiques selon le type d'action
            if action_type == "dice_roll" and "dice_result" in state:
                entry.update({
                    "dice_type": state["dice_result"].get("type", "normal"),
                    "dice_value": state["dice_result"].get("value"),
                    "dice_result": state["dice_result"],  # Garder le résultat complet
                    "next_section": state.get("decision", {}).get("next_section"),  # Ajout du next_section
                    "awaiting_action": state.get("decision", {}).get("awaiting_action", False),
                    "conditions": state.get("decision", {}).get("conditions", []),
                    "rules_summary": state.get("decision", {}).get("rules_summary", "")
                })
            elif action_type == "user_input" and "user_response" in state:
                entry.update({
                    "response": state["user_response"]
                })
            elif action_type == "decision" and "decision" in state:
                decision = state["decision"]
                entry.update({
                    "next_section": decision.get("next_section"),
                    "awaiting_action": decision.get("awaiting_action"),
                    "conditions": decision.get("conditions", []),
                    "rules_summary": decision.get("rules_summary", ""),
                    "decision": decision  # Garder la décision complète pour compatibilité
                })

            # Ajouter à l'historique et sauvegarder
            self.history.append(entry)
            self.save_history()
            
            # Mettre à jour l'état avec l'historique et les stats
            state.update({
                "trace": {
                    "history": self.history,
                    "stats": self.stats
                },
                "history": self.history,  # Pour compatibilité
                "stats": self.stats  # Pour compatibilité
            })
            
            # Retourner la structure complète
            return {
                "state": state,  # État avec trace inclus
                "history": self.history,  # Pour compatibilité avec les tests
                "stats": self.stats,      # Pour compatibilité avec les tests
                "trace": {
                    "history": self.history,
                    "stats": self.stats
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erreur dans TraceAgent.invoke: {str(e)}")
            return {"error": str(e)}
            
    async def ainvoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict:
        """
        Version asynchrone de invoke.
        """
        try:
            return await self.invoke(input_data)
        except Exception as e:
            self.logger.error(f"Erreur dans ainvoke: {str(e)}")
            return {"error": str(e)}
    
    async def get_character_stats(self) -> Dict:
        """
        Récupère les statistiques actuelles du personnage.
        
        Returns:
            Dict: Les statistiques du personnage
        """
        return self.stats.copy()
    
    async def update_stats(self, updates: Dict) -> None:
        """
        Met à jour les statistiques du personnage.
        
        Args:
            updates (Dict): Les mises à jour à appliquer aux stats
        """
        for category, values in updates.items():
            if category in self.stats:
                if isinstance(self.stats[category], dict):
                    self.stats[category].update(values)
                else:
                    self.stats[category] = values
            else:
                self.stats[category] = values
        
        # Sauvegarder les stats mises à jour
        self.save_adventure_stats()
        
        # Émettre un événement de mise à jour des stats
        await self.event_bus.emit(Event(
            type="stats_updated",
            data={"stats": self.stats.copy()}
        ))

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
