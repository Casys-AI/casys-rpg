# agents/story_graph.py

from typing import Dict, Optional, Any, List, AsyncGenerator, Union
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph import StateGraph
from event_bus import EventBus, Event
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
import asyncio
import logging

class GameState(BaseModel):
    """État du jeu pour le StateGraph."""
    section_number: int = Field(default=1)
    content: Optional[str] = None
    rules: Dict = Field(default_factory=lambda: {
        "needs_dice": False,
        "dice_type": "normal",
        "conditions": [],
        "next_sections": [],
        "rules_summary": ""
    })
    decision: Dict = Field(default_factory=lambda: {
        "awaiting_action": "user_input",
        "section_number": 1
    })
    stats: Optional[Dict] = None
    history: Optional[list] = None
    error: Optional[str] = None
    needs_content: bool = True
    user_response: Optional[str] = None
    dice_result: Optional[Dict] = None
    trace: Optional[Dict] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

class StoryGraph:
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
        self.event_bus = event_bus or EventBus()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Initialiser les agents avec l'EventBus
        self.narrator = narrator_agent or NarratorAgent(event_bus=self.event_bus)
        self.rules = rules_agent or RulesAgent(event_bus=self.event_bus)
        self.decision = decision_agent or DecisionAgent(event_bus=self.event_bus)
        self.trace = trace_agent or TraceAgent(event_bus=self.event_bus)

        # Création du workflow avec StateGraph
        self.graph = StateGraph(
            state_schema=GameState
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

    async def emit_event(self, event_type: str, data: Dict):
        """Centralise l'émission des événements."""
        try:
            await self.event_bus.emit(Event(type=event_type, data=data))
            self.logger.info(f"Événement émis : {event_type} avec données {data}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'émission de l'événement {event_type}: {str(e)}")

    async def invoke(self, state: Union[GameState, Dict], *args, **kwargs) -> AsyncGenerator[Dict, None]:
        """
        Point d'entrée principal du StoryGraph.
        Retourne un générateur asynchrone des états successifs.
        """
        try:
            self.logger.debug("Démarrage du StoryGraph")
            current_state = state.dict() if isinstance(state, GameState) else state
            
            # Initialiser l'EventBus avec l'état initial
            await self.event_bus.update_state(current_state)
            
            while True:
                # Exécuter le nœud de départ
                async for result in self._start_node(current_state):
                    yield result
                
                # Exécuter le nœud de décision
                async for result in self._decision_node(current_state):
                    yield result
                
                # Exécuter le nœud de trace
                async for result in self._trace_node(current_state):
                    yield result
                
                # Vérifier si on doit continuer
                should_continue = await self._should_continue(current_state)
                if not should_continue:
                    break
                
                # Mettre à jour l'état courant
                current_state = await self.event_bus.get_state()
                
        except Exception as e:
            self.logger.error(f"Erreur dans invoke: {str(e)}")
            await self.event_bus.update_state({"error": str(e)})
            yield await self.event_bus.get_state()

    async def _start_node(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """Point d'entrée du graphe."""
        self.logger.debug("Entrée dans _start_node")
        
        # Initialisation de l'état si nécessaire
        if not state:
            state = {}
        
        # S'assurer que trace existe toujours dans l'état
        if "trace" not in state:
            state["trace"] = {
                "stats": self.trace.stats if hasattr(self.trace, "stats") else {
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
                }
            }
            self.logger.debug(f"État initial créé avec trace: {state}")
        
        # Continuer avec le flux normal
        async for updated_state in self._process_state(state):
            yield updated_state

    async def _process_state(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """Nœud de départ qui combine NarratorAgent et RulesAgent."""
        self.logger.debug(f"Processing state with content: {state.get('content')}")
        self.logger.debug(f"Current trace content: {state.get('trace', {})}")
        
        try:
            # Log state before processing
            self.logger.debug(f"Pre-processing state: {state}")
            
            # Ensure section number is set
            section_number = state.get("section_number", 1)
            self.logger.debug(f"Processing section number: {section_number}")
            
            # Pour les sections > 1, vérifier la décision préalable
            if section_number > 1 and not state.get("decision"):
                yield state
                return
            
            # Préparer l'état pour le NarratorAgent
            narrator_input = {
                "state": {
                    "section_number": section_number,
                    "use_cache": state.get("use_cache", False)
                }
            }
            
            # Exécuter le NarratorAgent
            try:
                async for narrator_state in self.narrator.ainvoke(narrator_input):
                    # Mettre à jour l'état avec le résultat du NarratorAgent
                    state.update(narrator_state)
                    await self.emit_event("state_updated", state)
                    yield state
            except Exception as e:
                self.logger.error(f"Error in NarratorAgent: {str(e)}", exc_info=True)
                await self.event_bus.update_state({"error": str(e)})
                yield await self.event_bus.get_state()
                return
                
            # Exécuter le RulesAgent
            try:
                async for rules in self.rules.ainvoke({"section": section_number}):
                    if rules and "rules" in rules:
                        await self.event_bus.update_state(rules)
                        yield await self.event_bus.get_state()
            except Exception as e:
                self.logger.error(f"Error in RulesAgent: {str(e)}", exc_info=True)
                await self.event_bus.update_state({"error": str(e)})
                yield await self.event_bus.get_state()
                return
            
            # Log state after processing
            self.logger.debug(f"Post-processing state: {state}")
            
        except Exception as e:
            self.logger.error(f"Error in _process_state: {str(e)}", exc_info=True)
            state['error'] = str(e)
            yield state

    async def _decision_node(self, state: Dict) -> AsyncGenerator[Dict, None]:
        """Nœud de décision qui utilise le DecisionAgent."""
        try:
            self.logger.debug("Entrée dans _decision_node")
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
            self.logger.error(f"Erreur dans _decision_node: {str(e)}")
            await self.event_bus.update_state({"error": str(e)})
            yield await self.event_bus.get_state()

    async def _trace_node(self, state: Dict, *args, **kwargs) -> AsyncGenerator[Dict, None]:
        """Nœud du graph pour le TraceAgent."""
        try:
            self.logger.debug("Entrée dans _trace_node")
            current_state = await self.event_bus.get_state()
            
            # Vérifier qu'on a une décision
            decision = current_state.get("decision", {})
            if not decision or "awaiting_action" not in decision:
                self.logger.debug("Pas de décision pour TraceAgent")
                yield current_state
                return
            
            # Exécuter le TraceAgent
            async for result in self.trace.ainvoke(current_state):
                if result:
                    await self.event_bus.update_state(result)
                    yield await self.event_bus.get_state()
            
        except Exception as e:
            self.logger.error(f"Erreur dans _trace_node: {str(e)}")
            await self.event_bus.update_state({"error": str(e)})
            yield await self.event_bus.get_state()

    async def _should_continue(self, state: Dict) -> bool:
        """Détermine si le workflow doit continuer ou attendre une action du joueur."""
        try:
            # Si on a une erreur, on arrête
            if state.get("error"):
                self.logger.debug("Arrêt - Erreur détectée")
                return False

            # Si on n'a pas de décision, on arrête car on attend une action
            decision = state.get("decision", {})
            if not decision:
                self.logger.debug("Arrêt - En attente d'une décision")
                return False

            # Si on attend une action spécifique, on arrête aussi
            awaiting_action = decision.get("awaiting_action")
            if awaiting_action in ["user_input", "dice_roll"]:
                self.logger.debug(f"Arrêt - En attente de : {awaiting_action}")
                return False

            # Si on a une décision mais pas d'attente d'action, on continue
            self.logger.debug("Continuer - Décision prise sans attente d'action")
            return True

        except Exception as e:
            self.logger.error(f"Erreur dans _should_continue: {str(e)}")
            return False
