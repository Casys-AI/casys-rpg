# agents/story_graph.py

from typing import Dict, Optional
import logging
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph import StateGraph
from event_bus import EventBus, Event
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent

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

    def dict(self, *args, **kwargs):
        """Surcharge de la méthode dict pour un accès plus simple aux données."""
        d = super().model_dump(*args, **kwargs)
        return d

    def __getitem__(self, key):
        """Permet l'accès aux attributs comme un dictionnaire."""
        return getattr(self, key)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class StoryGraph:
    """
    Gestion hybride du flux de jeu utilisant StateGraph pour le workflow principal
    et EventBus pour les événements asynchrones.
    """
    def __init__(self, event_bus: EventBus, narrator_agent, rules_agent, decision_agent, trace_agent):
        """Initialise le StoryGraph avec les agents et l'event bus."""
        self.event_bus = event_bus
        self.narrator = narrator_agent
        self.rules = rules_agent
        self.decision = decision_agent
        self.trace = trace_agent
        self.logger = logging.getLogger(__name__)
        
        # Création du workflow avec StateGraph
        self.graph = StateGraph(state_schema=GameState)
        
        # Configuration des nœuds
        self.graph.add_node("narrator_node", self._narrator_node)
        self.graph.add_node("rules_node", self._rules_node)
        self.graph.add_node("decision_node", self._decision_node)
        self.graph.add_node("trace_node", self._trace_node)
        self.graph.add_node("end", lambda state: state)

        # Configuration du flux
        self.graph.set_entry_point("narrator_node")
        self.graph.add_edge("narrator_node", "rules_node")
        self.graph.add_edge("rules_node", "decision_node")
        self.graph.add_edge("decision_node", "trace_node")
        self.graph.add_conditional_edges(
            "trace_node",
            self.should_continue,
            {
                "narrator_node": "narrator_node",
                "end": "end"
            }
        )

        # Compiler le graphe
        self.graph = self.graph.compile()

    async def setup_event_listeners(self):
        """Configure les écouteurs d'événements de manière asynchrone."""
        await self.event_bus.subscribe("rules_generated", self.on_rules_generated)
        await self.event_bus.subscribe("content_generated", self.on_content_generated)
        await self.event_bus.subscribe("decision_made", self.on_decision_made)
        await self.event_bus.subscribe("trace_updated", self.on_trace_updated)

    async def emit_event(self, event_type: str, data: Dict):
        """Centralise l'émission des événements."""
        try:
            await self.event_bus.emit(Event(type=event_type, data=data))
            self.logger.info(f"Événement émis : {event_type} avec données {data}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'émission de l'événement {event_type}: {str(e)}")

    async def _error_handler(self, state: GameState, error: Exception) -> GameState:
        """Gère les erreurs dans le workflow."""
        state.error = str(error)
        self.logger.error(f"Erreur dans le workflow : {str(error)}")
        return state

    async def _narrator_node(self, state: GameState) -> Dict:
        """Nœud du graph pour le NarratorAgent."""
        try:
            if state.needs_content:
                async for result in self.narrator.astream(state.dict()):
                    if result and "content" in result:
                        await self.emit_event("content_generated", {
                            "section": state.section_number, 
                            "content": result["content"]
                        })
                        return result
            return {}
        except Exception as e:
            self.logger.error(f"Erreur dans le nœud narrator: {str(e)}")
            return {}

    async def _rules_node(self, state: GameState) -> Dict:
        """Nœud du graph pour le RulesAgent."""
        try:
            async for result in self.rules.astream(state.dict()):
                if result:
                    # Émettre l'événement avec les règles complètes
                    await self.emit_event("rules_generated", {
                        "section": state.section_number,
                        "rules": result
                    })
                    return result
            return state.rules
        except Exception as e:
            self.logger.error(f"Erreur dans le nœud rules: {str(e)}")
            return state.rules

    async def _decision_node(self, state: GameState) -> Dict:
        """Nœud du graph pour le DecisionAgent."""
        try:
            needs_dice = state.rules.get("needs_dice", False)
            
            if needs_dice and not state.dice_result:
                decision = {
                    "awaiting_action": "dice_roll",
                    "dice_type": state.rules.get("dice_type", "normal"),
                    "section_number": state.section_number
                }
                await self.emit_event("decision_made", {
                    "section": state.section_number,
                    "decision": decision
                })
                return decision
            
            if state.user_response or state.dice_result:
                async for result in self.decision.astream(state.dict()):
                    if result:
                        await self.emit_event("decision_made", {
                            "section": state.section_number,
                            "decision": result
                        })
                        return result
            
            # État par défaut
            decision = {
                "awaiting_action": "user_input",
                "section_number": state.section_number
            }
            await self.emit_event("decision_made", {
                "section": state.section_number,
                "decision": decision
            })
            return decision
            
        except Exception as e:
            self.logger.error(f"Erreur dans le nœud decision: {str(e)}")
            return {"awaiting_action": "user_input", "section_number": state.section_number}

    async def _trace_node(self, state: GameState) -> Dict:
        """Nœud du graph pour le TraceAgent."""
        try:
            async for result in self.trace.astream(state.dict()):
                if result:
                    await self.emit_event("trace_updated", {
                        "section": state.section_number,
                        "history": result.get("history"),
                        "stats": result.get("stats")
                    })
                    return result
            return {}
        except Exception as e:
            self.logger.error(f"Erreur dans le nœud trace: {str(e)}")
            return {}

    def should_continue(self, state: GameState) -> str:
        """Détermine si le workflow doit continuer ou attendre une action du joueur."""
        if state.error:
            self.logger.debug(f"Arrêt dû à une erreur : {state.error}")
            return "end"

        if state.decision:
            awaiting = state.decision.get("awaiting_action")
            
            # Si on attend une action du joueur (dé ou réponse)
            if awaiting in ["dice_roll", "user_input"]:
                self.logger.debug(f"Arrêt - En attente de : {awaiting}")
                return "end"

            # Si on a une décision complète
            next_section = state.decision.get("next_section")
            if next_section:
                # Éviter la récursion infinie
                if state.section_number == next_section:
                    self.logger.debug("Arrêt - Éviter la récursion infinie (section identique)")
                    return "end"

                # Préparer la prochaine section
                state.section_number = next_section
                state.needs_content = True
                state.user_response = None
                state.dice_result = None
                state.rules = {
                    "needs_dice": True,
                    "dice_type": "normal",
                    "conditions": [],
                    "next_sections": [],
                    "rules_summary": ""
                }
                state.decision = None
                self.logger.debug(f"Continuer vers la section suivante : {state.section_number}")
                return "narrator_node"

        self.logger.debug("Arrêt - Aucune condition pour continuer le workflow")
        return "end"

    async def invoke(self, state_dict: Dict):
        """
        Exécute le workflow avec l'état donné en utilisant le mode de streaming.
        """
        try:
            # Créer un nouvel état avec les valeurs par défaut
            state = GameState(**state_dict)
            final_state = state.dict()
            
            # S'assurer que les règles ont une valeur initiale
            if "rules" not in final_state:
                final_state["rules"] = {
                    "needs_dice": True,
                    "dice_type": "normal",
                    "conditions": [],
                    "next_sections": [],
                    "rules_summary": ""
                }
            
            # Exécuter le workflow avec stream_mode="updates"
            async for output in self.graph.astream(state, stream_mode="updates"):
                # output contient les résultats de chaque nœud
                for node_name, node_output in output.items():
                    if not node_output:  # Ignorer les sorties vides
                        continue
                        
                    if node_name == "narrator_node":
                        if "content" in node_output:
                            final_state["content"] = node_output["content"]
                            final_state["needs_content"] = False
                    
                    elif node_name == "rules_node":
                        # Mettre à jour les règles avec les nouvelles valeurs
                        final_state["rules"] = {
                            "needs_dice": node_output.get("needs_dice", True),  # Par défaut True
                            "dice_type": node_output.get("dice_type", "normal"),
                            "conditions": node_output.get("conditions", []),
                            "next_sections": node_output.get("next_sections", []),
                            "rules_summary": node_output.get("rules_summary", "")
                        }
                    
                    elif node_name == "decision_node":
                        if node_output:
                            final_state["decision"] = node_output
                            if "next_section" in node_output:
                                final_state["section_number"] = node_output["next_section"]
                                final_state["dice_result"] = None
                                final_state["user_response"] = None
                                final_state["needs_content"] = True
                                final_state["rules"] = {
                                    "needs_dice": True,
                                    "dice_type": "normal",
                                    "conditions": [],
                                    "next_sections": [],
                                    "rules_summary": ""
                                }
                    
                    elif node_name == "trace_node":
                        if "history" in node_output:
                            final_state["history"] = node_output["history"]
                        if "stats" in node_output:
                            final_state["stats"] = node_output["stats"]

            # Retourner l'état final sans les valeurs None
            return {k: v for k, v in final_state.items() if v is not None}
            
        except Exception as e:
            self.logger.error(f"StoryGraph - Erreur lors de l'exécution: {str(e)}")
            raise

    async def on_rules_generated(self, event: Event):
        """Gestionnaire d'événement pour rules_generated."""
        self.logger.info(f"Règles générées pour la section {event.data.get('section')}")

    async def on_content_generated(self, event: Event):
        """Gestionnaire d'événement pour content_generated."""
        self.logger.info(f"Contenu généré pour la section {event.data.get('section')}")

    async def on_decision_made(self, event: Event):
        """Gestionnaire d'événement pour decision_made."""
        self.logger.info(f"Décision prise pour la section {event.data.get('section')}")

    async def on_trace_updated(self, event: Event):
        """Gestionnaire d'événement pour trace_updated."""
        self.logger.info(f"Trace mise à jour pour la section {event.data.get('section')}")
