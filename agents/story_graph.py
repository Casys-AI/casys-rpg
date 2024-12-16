# agents/story_graph.py

from typing import Dict, Optional, Any, List, AsyncGenerator, Union
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, ConfigDict
from langgraph.graph import StateGraph
from event_bus import EventBus, Event
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from agents.models import GameState
from agents.base_agent import BaseAgent
import asyncio
import logging
import json
from logging_config import setup_logging
import os

# Configuration du logging
setup_logging()
logger = logging.getLogger('story_graph')

class StoryGraph(BaseAgent):
    """
    Gestion hybride du flux de jeu utilisant StateGraph pour le workflow principal
    et EventBus pour les événements asynchrones.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        narrator_agent: Optional[NarratorAgent] = None,
        rules_agent: Optional[RulesAgent] = None,
        decision_agent: Optional[DecisionAgent] = None,
        trace_agent: Optional[TraceAgent] = None
    ):
        """
        Initialise le StoryGraph avec les agents et l'EventBus.
        
        Args:
            event_bus: Bus d'événements pour la communication entre composants
            narrator_agent: Agent pour la narration, si None un nouveau sera créé
            rules_agent: Agent pour les règles, si None un nouveau sera créé
            decision_agent: Agent pour les décisions, si None un nouveau sera créé
            trace_agent: Agent pour le traçage, si None un nouveau sera créé
        """
        # Initialiser le bus d'événements
        event_bus = event_bus or EventBus()
        super().__init__(event_bus)  # Appel au constructeur parent avec le bus
        
        # Initialiser les agents avec l'EventBus
        self.narrator = narrator_agent or NarratorAgent(event_bus=self.event_bus)
        self.rules = rules_agent or RulesAgent(event_bus=self.event_bus)
        self.decision = decision_agent or DecisionAgent(event_bus=self.event_bus)
        self.trace = trace_agent or TraceAgent(event_bus=self.event_bus)

        # Création du workflow avec StateGraph
        self.graph = StateGraph(
            state_schema=Dict[str, Any]  # Utiliser un schéma de dictionnaire générique
        )

        # Configuration des nœuds
        self.graph.add_node("start_node", self._start_node)
        self.graph.add_node("decision_node", self._decision_node)
        self.graph.add_node("trace_node", self._trace_node)
        self.graph.add_node("end_node", lambda x: x)

        # Configuration du flux
        self.graph.set_entry_point("start_node")
        self.graph.add_edge("start_node", "decision_node")
        self.graph.add_edge("decision_node", "trace_node")
        
        # Configuration des conditions de fin
        self.graph.set_finish_point("end_node")
        self.graph.add_conditional_edges(
            "trace_node",
            self._should_continue,
            {
                True: "start_node",
                False: "end_node"
            }
        )

        # Compiler le graphe
        self.graph = self.graph.compile()
        
        # État interne
        self.last_error = None

    def truncate_for_log(self, content: str, max_length: int = 100) -> str:
        """Tronque une chaîne pour les logs."""
        if not content or len(str(content)) <= max_length:
            return str(content)
        return str(content)[:max_length] + "..."
        
    def check_section_cache(self, section_number: int) -> bool:
        """
        Vérifie si une section est en cache.
        
        Args:
            section_number: Numéro de la section à vérifier
            
        Returns:
            bool: True si la section est en cache
        """
        cache_file = os.path.join("data/sections/cache", f"{section_number}_cached.md")
        return os.path.exists(cache_file)
        
    def get_character_stats(self) -> Dict:
        """
        Retourne les statistiques actuelles du personnage.
        
        Returns:
            Dict avec les stats du personnage depuis le fichier de trace
        """
        try:
            return self.trace.get_character_stats()
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erreur dans get_character_stats: {str(e)}")
            return {"error": str(e)}

    async def emit_event(self, event_type: str, data: Dict):
        """Centralise l'émission des événements."""
        try:
            await self.event_bus.emit(Event(type=event_type, data=data))
            logger.debug(f"Événement émis : {event_type} avec données {data}")
        except Exception as e:
            logger.error(f"Erreur lors de l'émission de l'événement {event_type}: {str(e)}")

    async def invoke(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """
        Traite l'état du jeu à travers les différents agents.
        
        Args:
            state: État du jeu actuel
            
        Returns:
            AsyncGenerator[Dict, None]: Générateur d'états de jeu
        """
        try:
            # Initialiser le GameState
            if state is None:
                state = {
                    "section_number": 1,
                    "formatted_content": None,
                    "current_section": {
                        "number": 1,
                        "content": None,
                        "choices": [],
                        "stats": {}
                    },
                    "rules": {
                        "needs_dice": True,
                        "dice_type": "normal",
                        "conditions": [],
                        "next_sections": [],
                        "rules_summary": ""
                    },
                    "decision": {
                        "awaiting_action": "user_input",
                        "section_number": 1
                    },
                    "stats": None,
                    "history": [],
                    "error": None,
                    "needs_content": True,
                    "user_response": None,
                    "dice_result": None,
                    "trace": {
                        "stats": {
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
                        },
                        "history": []
                    }
                }
            
            game_state = GameState(**state)
            
            # Si on a besoin de contenu
            if game_state.needs_content:
                # Obtenir le contenu via NarratorAgent
                narrator_result = await self.narrator.invoke({"state": game_state.model_dump()})
                if "error" in narrator_result:
                    yield narrator_result
                    return
                    
                # Mettre à jour l'état avec le contenu formaté
                game_state.formatted_content = narrator_result["state"]["formatted_content"]
                game_state.needs_content = False
                
            # Obtenir les règles via RulesAgent
            if not game_state.rules:
                rules_result = await self.rules.invoke({"state": game_state.model_dump()})
                if "error" in rules_result:
                    yield rules_result
                    return
                    
                # Mettre à jour l'état avec les règles
                game_state.rules = rules_result["state"]["rules"]
                
            # Obtenir la décision via DecisionAgent
            if game_state.user_response:
                decision_result = await self.decision.invoke({"state": game_state.model_dump()})
                if "error" in decision_result:
                    yield decision_result
                    return
                    
                # Mettre à jour l'état avec la décision
                game_state.decision = decision_result["state"]["decision"]
                
            # Obtenir la trace via TraceAgent si nécessaire
            if not game_state.trace or "stats" not in game_state.trace:
                trace_result = await self.trace.invoke({"state": game_state.model_dump()})
                if "error" in trace_result:
                    yield trace_result
                    return
                
                # Mettre à jour l'état avec la trace
                game_state.trace = trace_result.get("state", {}).get("trace", {})
                if not game_state.trace or "stats" not in game_state.trace:
                    game_state.trace = {
                        "stats": {
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
                        }
                    }
                
            # Mettre à jour la trace
            await self.trace.invoke({"state": game_state.model_dump()})
            
            # Retourner l'état final
            yield {"state": game_state.model_dump()}
            
        except Exception as e:
            logger.error(f"Error in StoryGraph.invoke: {str(e)}")
            yield {"error": str(e)}

    async def _start_node(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """Point d'entrée du graphe."""
        logger.debug("Entrée dans _start_node")
        
        try:
            # Initialisation de l'état avec GameState
            if not state:
                initial_state = GameState(
                    section_number=1,
                    formatted_content=None,
                    current_section={
                        "number": 1,
                        "content": None,
                        "choices": [],
                        "stats": {}
                    },
                    rules={
                        "needs_dice": True,
                        "dice_type": "normal",
                        "conditions": [],
                        "next_sections": [],
                        "rules_summary": ""
                    },
                    decision={
                        "awaiting_action": "user_input",
                        "section_number": 1
                    },
                    stats=None,
                    history=[],
                    error=None,
                    needs_content=True,
                    user_response=None,
                    dice_result={},  # Initialiser avec un dictionnaire vide
                    trace={
                        "stats": {
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
                        },
                        "history": []
                    }
                )
                state = initial_state.model_dump()
                logger.debug(f"État initial créé: {state}")

            # Continuer avec le flux normal
            async for updated_state in self._process_state(state):
                yield updated_state
                
        except Exception as e:
            logger.error(f"Erreur dans _start_node: {str(e)}")
            yield {"error": str(e)}

    async def _process_state(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """Nœud de départ qui combine NarratorAgent et RulesAgent."""
        logger.debug(f"Processing state with content: {state.get('content')}")
        logger.debug(f"Current trace content: {state.get('trace', {})}")
        
        try:
            # Log state before processing
            logger.debug(f"Pre-processing state: {state}")
            
            # Ensure section number is set
            section_number = state.get("section_number", 1)
            logger.debug(f"Processing section number: {section_number}")
            
            # Pour les sections > 1, vérifier la décision préalable
            if section_number > 1 and not state.get("decision"):
                state["error"] = "No decision found for section > 1"
                await self.event_bus.update_state(state)
                yield state
                return

            # Utiliser NarratorAgent pour obtenir le contenu
            try:
                async for narrator_state in self.narrator.ainvoke(state):
                    await self.emit_event("state_updated", narrator_state)
                    # Fusionner l'état au lieu de le remplacer
                    state.update(narrator_state)
            except Exception as e:
                logger.error(f"Error in NarratorAgent: {str(e)}", exc_info=True)
                state["error"] = str(e)
                await self.event_bus.update_state(state)
                yield state
                return

            # Utiliser RulesAgent pour analyser les règles
            try:
                async for rules in self.rules.ainvoke(state):
                    await self.emit_event("state_updated", rules)
                    # Fusionner l'état au lieu de le remplacer
                    state.update(rules)
            except Exception as e:
                logger.error(f"Error in RulesAgent: {str(e)}", exc_info=True)
                state["error"] = str(e)
                await self.event_bus.update_state(state)
                yield state
                return
            
            # Log state after processing
            logger.debug(f"Post-processing state: {state}")
            await self.event_bus.update_state(state)
            yield state
            
        except Exception as e:
            logger.error(f"Error in _process_state: {str(e)}", exc_info=True)
            state["error"] = str(e)
            await self.event_bus.update_state(state)
            yield state

    async def _decision_node(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """Nœud de décision qui utilise le DecisionAgent."""
        try:
            logger.debug("Entrée dans _decision_node")
            current_state = await self.event_bus.get_state()
            
            # Vérifier si une décision est nécessaire
            rules = current_state.get("rules", {})
            if not rules:
                yield current_state
                return
                
            # Exécuter le DecisionAgent
            async for result in self.decision.ainvoke({"rules": rules}):
                if result and "decision" in result:
                    # S'assurer que awaiting_action a une valeur par défaut
                    if result["decision"].get("awaiting_action") is None:
                        result["decision"]["awaiting_action"] = "choice"
                    await self.event_bus.update_state(result)
                    yield await self.event_bus.get_state()
            
        except Exception as e:
            logger.error(f"Erreur dans _decision_node: {str(e)}")
            await self.event_bus.update_state({"error": str(e)})
            yield await self.event_bus.get_state()

    async def _trace_node(self, state: Dict, *args, **kwargs) -> AsyncGenerator[Dict, None]:
        """Nœud du graph pour le TraceAgent."""
        try:
            logger.debug("Entrée dans _trace_node")
            current_state = await self.event_bus.get_state()
            
            # Vérifier qu'on a une décision
            decision = current_state.get("decision", {})
            if not decision or "awaiting_action" not in decision:
                logger.debug("Pas de décision pour TraceAgent")
                yield current_state
                return
            
            # Exécuter le TraceAgent
            async for result in self.trace.ainvoke(current_state):
                if result:
                    await self.event_bus.update_state(result)
                    yield await self.event_bus.get_state()
            
        except Exception as e:
            logger.error(f"Erreur dans _trace_node: {str(e)}")
            await self.event_bus.update_state({"error": str(e)})
            yield await self.event_bus.get_state()

    async def _should_continue(self, state: Dict) -> bool:
        """Détermine si le workflow doit continuer ou attendre une action du joueur."""
        try:
            # Si on a une erreur, on arrête
            if state.get("error"):
                logger.debug("Arrêt - Erreur détectée")
                return False

            # Si on n'a pas de décision, on arrête car on attend une action
            decision = state.get("decision", {})
            if not decision:
                logger.debug("Arrêt - En attente d'une décision")
                return False

            # Si on attend une action spécifique, on arrête aussi
            awaiting_action = decision.get("awaiting_action")
            if awaiting_action in ["user_input", "dice_roll"]:
                logger.debug(f"Arrêt - En attente de : {awaiting_action}")
                return False

            # Si on a une décision mais pas d'attente d'action, on continue
            logger.debug("Continuer - Décision prise sans attente d'action")
            return True

        except Exception as e:
            logger.error(f"Erreur dans _should_continue: {str(e)}")
            return False
