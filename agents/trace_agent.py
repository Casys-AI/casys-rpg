from typing import Dict, Optional, Any, List
from pydantic import BaseModel, ConfigDict, Field
from event_bus import EventBus, Event
from agents.models import GameState
from datetime import datetime
import logging
import json
from pathlib import Path
import shutil
from agents.base_agent import BaseAgent

class TraceConfig(BaseModel):
    """Configuration pour TraceAgent."""
    trace_directory: str = Field(default="data/trace")
    initial_stats: Dict = Field(default_factory=lambda: {
        "Caractéristiques": {
            "Habileté": 10,
            "Chance": 5,
            "Endurance": 8
        },
        "Ressources": {
            "Or": 100
        },
        "Inventaire": {
            "Objets": ["Épée", "Bouclier"]
        }
    })
    model_config = ConfigDict(arbitrary_types_allowed=True)

class TraceAgent(BaseAgent):
    """Agent responsable du traçage."""

    def __init__(self, event_bus: EventBus, config: Optional[TraceConfig] = None, **kwargs):
        """
        Initialise l'agent avec une configuration Pydantic.
        
        Args:
            event_bus: Bus d'événements
            config: Configuration Pydantic (optionnel)
            **kwargs: Arguments supplémentaires pour la configuration
        """
        super().__init__(event_bus)  # Appel au constructeur parent
        self.config = config or TraceConfig(**kwargs)
        self.trace_directory = Path(self.config.trace_directory)
        self._session_dir = self.create_session_dir()
        self.history = []
        self.stats = self.config.initial_stats.copy()
        self.save_adventure_stats()
        self.save_history()
    
    def create_session_dir(self) -> Path:
        """Crée le répertoire de session pour cette partie"""
        # Supprimer les anciens dossiers de session si nécessaire
        if self.trace_directory.exists():
            for old_dir in self.trace_directory.glob("game_*"):
                if old_dir.is_dir():
                    shutil.rmtree(old_dir)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.trace_directory / f"game_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def save_adventure_stats(self) -> None:
        """Sauvegarde les statistiques de l'aventure"""
        stats_file = self._session_dir / "adventure_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def save_history(self) -> None:
        """Sauvegarde l'historique des actions"""
        history_file = self._session_dir / "history.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def validate_state(self, state: Dict) -> Dict:
        """Valide et corrige l'état si nécessaire."""
        logging.getLogger(__name__).debug(f"Validating state: {state}")
        
        if not state:
            state = {}
        
        # S'assurer que trace existe
        if 'trace' not in state or state['trace'] is None:
            state['trace'] = {}
            
        # S'assurer que stats existe dans trace
        if 'stats' not in state['trace']:
            logging.getLogger(__name__).warning("Stats missing in trace, restoring from agent defaults")
            state['trace']['stats'] = self.stats.copy()
            
        # Valider la structure des stats
        stats = state['trace'].get('stats', {})
        if not isinstance(stats, dict):
            logging.getLogger(__name__).error(f"Invalid stats type: {type(stats)}")
            stats = self.stats.copy()
            
        # S'assurer que toutes les catégories requises existent
        for category in ['Caractéristiques', 'Ressources', 'Inventaire']:
            if category not in stats:
                logging.getLogger(__name__).warning(f"Missing category {category} in stats")
                stats[category] = self.stats[category].copy()
                
        state['trace']['stats'] = stats
        logging.getLogger(__name__).debug(f"Validated state: {state}")
        return state

    async def invoke(self, input_data: Dict) -> Dict:
        """
        Enregistre une action dans l'historique et met à jour les stats si nécessaire.
        
        Args:
            input_data (Dict): Données de l'action avec state
            
        Returns:
            Dict: État mis à jour avec historique et stats
        """
        try:
            # Valider l'état d'abord
            state = self.validate_state(input_data.get("state", {}))
            
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
            if action_type == "dice_roll":
                dice_result = state.get("dice_result", {})
                if dice_result is not None:
                    entry.update({
                        "dice_type": dice_result.get("type", "normal"),
                        "dice_value": dice_result.get("value"),
                        "dice_result": dice_result,  # Garder le résultat complet
                        "next_section": state.get("decision", {}).get("next_section"),
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
            self.save_history()  # Plus d'await car la méthode n'est pas async
            
            # Émettre l'événement
            event = Event(
                type="state_traced",
                data={
                    "history_entry": entry,
                    "history_length": len(self.history)
                }
            )
            await self.event_bus.emit(event)
            
            # Mettre à jour l'état avec l'historique et les stats
            state["history"] = self.history
            state["trace"] = {
                "stats": self.stats,
                "history": self.history
            }
            
            return {
                "state": state,
                "history": self.history,  # Pour compatibilité
                "stats": self.stats,      # Pour compatibilité
                "trace": {
                    "history": self.history,
                    "stats": self.stats
                }
            }
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Erreur dans TraceAgent.invoke: {str(e)}", exc_info=True)
            return {
                "state": {
                    "error": str(e),
                    "history": self.history,  # Ajout de la clé history
                    "trace": {
                        "history": self.history,
                        "stats": self.stats
                    }
                }
            }
    
    async def ainvoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict:
        """
        Version asynchrone de invoke.
        """
        try:
            state = input_data.get("state", input_data)
            logging.getLogger(__name__).debug(f"Validating state: {state}")
            
            # Valider et corriger l'état
            state = self.validate_state(state)
            logging.getLogger(__name__).debug(f"Validated state: {state}")
            
            # Déterminer le type d'action
            action_type = "unknown"
            if "dice_result" in state:
                action_type = "dice_roll"
            elif "user_response" in state:
                action_type = "user_input"
            elif "decision" in state:
                action_type = "decision"
            
            # Créer l'entrée de base
            entry = {
                "timestamp": datetime.now().isoformat(),
                "section": state.get("section_number", 1),
                "action_type": action_type
            }
            
            # Ajouter les détails spécifiques à l'action
            if action_type == "dice_roll" and "dice_result" in state:
                entry.update({
                    "dice_type": state.get("rules", {}).get("dice_type", "normal"),
                    "result": state["dice_result"]
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
            self.save_history()  # Plus d'await car la méthode n'est pas async
            
            # Émettre l'événement
            event = Event(
                type="state_traced",
                data={
                    "history_entry": entry,
                    "history_length": len(self.history)
                }
            )
            await self.event_bus.emit(event)
            
            # Mettre à jour l'état avec l'historique
            state["history"] = self.history
            state["trace"] = {
                "stats": self.stats,
                "history": self.history
            }
            
            return state
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Erreur dans TraceAgent.invoke: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "history": self.history,
                "trace": {
                    "stats": self.stats,
                    "history": self.history
                }
            }
    
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
        stats_file = self._session_dir / "adventure_stats.json"
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
