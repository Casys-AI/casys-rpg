"""
Story Graph Module
Handles game workflow and state transitions.
"""

import logging
from typing import Dict, Optional, Any, AsyncGenerator
from datetime import datetime
from pydantic import Field
from langchain.schema.runnable import RunnableSerializable
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from typing_extensions import Annotated

from models.game_state import GameState, GameStateInput, GameStateOutput
from agents.base_agent import BaseAgent
from agents.protocols import (
    NarratorAgentProtocol,
    RulesAgentProtocol,
    DecisionAgentProtocol,
    TraceAgentProtocol,
    StoryGraphProtocol
)
from managers.protocols.state_manager_protocol import StateManagerProtocol
from config.agents.agent_config_base import AgentConfigBase
from models.errors_model import GameError, RulesError, StateError, NarratorError, DecisionError, TraceError
from models.trace_model import ActionType
from models.rules_model import RulesModel, DiceType, SourceType as RulesSourceType

logger = logging.getLogger(__name__)

class StoryGraph(BaseAgent):
    """Manages the game workflow and state transitions."""
    model_config = Field(arbitrary_types_allowed=True)
    config: AgentConfigBase = Field(default_factory=AgentConfigBase)
    state_manager: StateManagerProtocol
    narrator_agent: NarratorAgentProtocol
    rules_agent: RulesAgentProtocol
    decision_agent: DecisionAgentProtocol
    trace_agent: TraceAgentProtocol
    _graph: Optional[StateGraph] = None
    _current_section: int = 1

    def __init__(
        self,
        config: AgentConfigBase,
        narrator_agent: NarratorAgentProtocol,
        rules_agent: RulesAgentProtocol,
        decision_agent: DecisionAgentProtocol,
        trace_agent: TraceAgentProtocol,
        state_manager: StateManagerProtocol,
    ) -> None:
        """
        Initialize StoryGraph.
        
        Args:
            config: Configuration for the agent
            narrator_agent: Agent for narrative content
            rules_agent: Agent for rules analysis
            decision_agent: Agent for decision processing
            trace_agent: Agent for game history
            state_manager: Manager for game state
        """
        super().__init__(config=config)
        self.narrator_agent = narrator_agent
        self.rules_agent = rules_agent
        self.decision_agent = decision_agent
        self.trace_agent = trace_agent
        self.state_manager = state_manager
        self._graph = None
        self._current_section = 1

    async def execute_game_workflow(self, state: GameState) -> GameState:
        """
        Execute the main game workflow for a given state.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: Updated state after workflow execution
        """
        try:
            # Setup workflow if not initialized
            if not self._graph:
                await self._setup_workflow()
            
            # Execute workflow
            result = await self._process_workflow(state.model_dump())
            return GameState(**result)
        except Exception as e:
            logger.error(f"Error executing game workflow: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def validate_state_transition(self, from_state: GameState, to_state: GameState) -> bool:
        """
        Validate if a state transition is legal.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Returns:
            bool: True if transition is valid
        """
        try:
            # Get rules for current section
            rules = await self.rules_agent.process_section_rules(
                from_state.section_number,
                from_state.narrative.content if from_state.narrative else ""
            )
            
            # Check if transition is allowed
            return to_state.section_number in rules.next_sections
        except Exception as e:
            logger.error(f"Error validating state transition: {e}")
            return False

    async def process_game_section(self, section_number: int) -> GameState:
        """Process a complete game section."""
        try:
            # Get narrative content through narrator agent
            narrative_result = await self.narrator_agent.process_section(section_number)
            if isinstance(narrative_result, NarratorError):
                return await self.state_manager.create_error_state(
                    section_number=section_number,
                    error=narrative_result.message
                )
            
            # Get rules through rules agent
            rules_result = await self.rules_agent.process_section_rules(
                section_number,
                narrative_result.content if narrative_result else ""
            )
            
            # Create state with results
            state = GameState.create_initial_state().with_updates(
                section_number=section_number,
                narrative=narrative_result,
                rules=rules_result
            )
            
            # Execute workflow
            return await self.execute_game_workflow(state)
            
        except Exception as e:
            logger.error(f"Error processing game section: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def apply_section_rules(self, state: GameState) -> GameState:
        """Apply game rules to the current state."""
        try:
            # Process rules
            rules = await self.rules_agent.process_section_rules(
                state.section_number,
                state.narrative.content if state.narrative else ""
            )
            
            if isinstance(rules, RulesError):
                return await self.state_manager.create_error_state(
                    section_number=state.section_number,
                    error=rules.message
                )
                
            # Update state with rules
            state.rules = rules
            return state
        except Exception as e:
            logger.error(f"Error applying section rules: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def merge_agent_results(self, results: Dict[str, Any]) -> GameState:
        """
        Merge results from multiple agents into a single state.
        
        Args:
            results: Dictionary of agent results
            
        Returns:
            GameState: Merged game state
        """
        try:
            narrative = results.get("narrator")
            rules = results.get("rules")
            decision = results.get("decision")
            trace = results.get("trace")
            
            # Vérifier si narrative est une erreur
            if isinstance(narrative, NarratorError):
                return await self.state_manager.create_error_state(
                    section_number=self._current_section,
                    error=narrative.message
                )
            
            # Créer un état initial avec section_number
            section_number = (
                narrative.section_number if narrative and hasattr(narrative, 'section_number')
                else self._current_section
            )
            
            # Vérifier les autres erreurs
            for result, error_type in [
                (rules, RulesError),
                (decision, DecisionError),
                (trace, TraceError)
            ]:
                if isinstance(result, error_type):
                    return await self.state_manager.create_error_state(
                        section_number=section_number,
                        error=result.message
                    )
            
            # Créer l'état de base
            base_state = GameState.create_initial_state().with_updates(
                section_number=section_number
            )
            
            # Ajouter les résultats des agents s'ils existent
            updates = {}
            if narrative:
                updates["narrative"] = narrative
            if rules:
                updates["rules"] = rules
            if decision:
                updates["decision"] = decision
            if trace:
                updates["trace"] = trace
                
            # Mettre à jour l'état avec les résultats
            return base_state.with_updates(**updates)
            
        except Exception as e:
            logger.error(f"Error merging agent results: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def start_session(self) -> GameState:
        """Démarre une nouvelle session de jeu."""
        try:
            logger.info("Starting story graph session...")
            
            # Initialize state manager
            await self.state_manager.initialize()
            
            # Configurer le workflow
            await self._setup_workflow()
            
            # Traiter le workflow et récupérer le dernier état
            final_state = None
            async for state in self._process_workflow({}):
                final_state = state
            
            if final_state is None:
                raise ValueError("Workflow did not produce a final state")
                
            logger.info("Story graph session started successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Failed to start story graph session: {e}")
            raise await self.state_manager.create_error_state(str(e))

    async def stop_session(self):
        """Arrête proprement la session de jeu."""
        try:
            logger.info("Stopping story graph session...")
            await self._cleanup_workflow()
            logger.info("Story graph session stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping story graph session: {e}")
            raise await self.state_manager.create_error_state(str(e))

    async def _cleanup_workflow(self):
        """Nettoie les ressources du workflow."""
        try:
            if self._graph:
                # Réinitialiser simplement la référence
                self._graph = None
            logger.info("Workflow cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up workflow: {e}")
            raise await self.state_manager.create_error_state(str(e))

    async def _setup_workflow(self) -> None:
        """Configure le workflow langgraph."""
        try:
            # Utiliser les modèles Pydantic pour input/output
            self._graph = StateGraph(
                GameState,
                input=GameStateInput,
                output=GameStateOutput
            )
            
            # Définir les noms des nœuds de manière cohérente
            # Préfixer les noms pour éviter les conflits avec les clés d'état
            INIT_NODE = "node_initialize"
            NARRATOR_NODE = "node_narrator"
            RULES_NODE = "node_rules"
            DECISION_NODE = "node_decision"
            TRACE_NODE = "node_trace"
            
            # Ajouter les agents comme nœuds
            # Utiliser des fonctions asynchrones directement
            self._graph.add_node(INIT_NODE, self._initialize_state)
            self._graph.add_node(NARRATOR_NODE, self._process_narrative)
            self._graph.add_node(RULES_NODE, self._process_rules)
            self._graph.add_node(DECISION_NODE, self._process_decision)
            self._graph.add_node(TRACE_NODE, self._process_trace)
            
            # Définir un flux linéaire simple pour déboguer
            self._graph.add_edge(START, INIT_NODE)
            self._graph.add_edge(INIT_NODE, NARRATOR_NODE)
            self._graph.add_edge(NARRATOR_NODE, RULES_NODE)
            self._graph.add_edge(RULES_NODE, DECISION_NODE)
            self._graph.add_edge(DECISION_NODE, TRACE_NODE)
            self._graph.add_edge(TRACE_NODE, END)
            
            # Compiler avec config async
            self._graph.compile()
            
            logger.info("Workflow setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up workflow: {e}")
            raise await self.state_manager.create_error_state(str(e))

    async def _initialize_state(self, state: GameState) -> GameState:
        """Initialize game state."""
        try:
            if state is None:
                state = await self.state_manager.create_initial_state()
            return state
        except Exception as e:
            logger.error(f"Error initializing state: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def _process_narrative(self, state: GameState) -> GameState:
        """Process narrative content."""
        try:
            # Get narrative content through agent
            narrative = await self.narrator_agent.process_section(state.section_number)
            if isinstance(narrative, NarratorError):
                return await self.state_manager.create_error_state(narrative.message)
                
            # Update state with narrative
            state.narrative = narrative
            return state
            
        except Exception as e:
            logger.error(f"Error processing narrative: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def _process_rules(self, state: GameState) -> GameState:
        """Process game rules."""
        try:
            # Get rules through agent
            rules = await self.rules_agent.process_section_rules(
                state.section_number,
                state.narrative.content if state.narrative else ""
            )
            
            if isinstance(rules, RulesError):
                return await self.state_manager.create_error_state(
                    section_number=state.section_number,
                    error=rules.message
                )
                
            # Update state with rules
            state.rules = rules
            return state
            
        except Exception as e:
            logger.error(f"Error processing rules: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def _process_decision(self, state: GameState) -> GameState:
        """Process player decision."""
        try:
            # Traiter la décision
            updated_state = await self.decision_agent.analyze_decision(state)
            return updated_state
        except Exception as e:
            logger.error(f"Error processing decision: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def _process_trace(self, state: GameState) -> GameState:
        """Process game trace."""
        try:
            # Enregistrer la trace
            await self.trace_agent.record_state(state)
            return state
        except Exception as e:
            logger.error(f"Error processing trace: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def navigate_to_section(self, section_number: int) -> GameState:
        """
        Navigate to a specific section.
        
        Args:
            section_number: Section number to navigate to
            
        Returns:
            GameState: Updated game state
        """
        try:
            # Validate section number
            if section_number < 1:
                raise ValueError("Section number must be positive")
                
            # Create state for the section
            state = GameState(section_number=section_number)
            
            # Process the section
            return await self.process_game_section(section_number)
            
        except Exception as e:
            logger.error(f"Error navigating to section {section_number}: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def process_user_input(self, input_text: str) -> GameState:
        """
        Process user input/response.
        
        Args:
            input_text: User's input text
            
        Returns:
            GameState: Updated game state
        """
        try:
            # Get current state
            current_state = await self.state_manager.get_current_state()
            if not current_state:
                raise ValueError("No current game state")
                
            # Update state with user input
            current_state.player_input = input_text
            
            # Process the updated state
            return await self.execute_game_workflow(current_state)
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def stream_game_state(self) -> AsyncGenerator[Dict, None]:
        """Stream l'état du jeu à chaque étape du workflow."""
        try:
            # Démarrer avec un état vide, le noeud start l'initialisera
            async for state in self._process_workflow({}, stream=True):
                yield state
        except Exception as e:
            logger.error(f"Error streaming game state: {e}")
            yield await self.state_manager.create_error_state(str(e))

    async def _process_workflow(self, initial_state: Dict, stream: bool = False):
        """
        Process the workflow with optional streaming.
        
        Args:
            initial_state: État initial pour le workflow
            stream: Si True, retourne chaque état intermédiaire
            
        Yields:
            GameState: États du workflow (intermédiaires si stream=True, sinon état final)
        """
        try:
            # Convertir l'état initial si nécessaire
            if not initial_state:
                initial_state = (await self.state_manager.create_initial_state()).model_dump()
            
            logger.info(f"Starting workflow with initial state: {initial_state}")
            
            # Exécuter le workflow
            final_state = None
            
            try:
                # Utiliser ainvoke pour l'exécution asynchrone
                workflow = self._graph.compile()
                result = await workflow.ainvoke(initial_state)
                logger.info(f"Workflow result: {result}")
                
                if isinstance(result, dict):
                    current_state = GameState.model_validate(result)
                    success = await self.state_manager.update_state(current_state)
                    if success:
                        final_state = current_state
                        logger.info(f"State updated successfully: {current_state}")
                    else:
                        logger.error("Failed to update state")
                        raise ValueError("Failed to update state")
                else:
                    logger.error(f"Unexpected result type: {type(result)}")
                    raise ValueError(f"Unexpected result type from workflow: {type(result)}")
                
            except AttributeError as e:
                logger.error(f"Workflow execution error: {e}")
                raise ValueError("Failed to execute workflow. Make sure all nodes are properly configured for async operation.")
            
            if final_state is None:
                logger.error("No final state produced")
                raise ValueError("Workflow did not produce a final state")
                
            yield final_state
                
        except GameError as e:
            logger.error(f"Domain error in workflow processing: {e}")
            yield await self.state_manager.create_error_state(str(e))
        except Exception as e:
            logger.error(f"Error in workflow processing: {e}")
            yield await self.state_manager.create_error_state(str(e))

# Add runtime type checking for protocol
StoryGraphProtocol.register(StoryGraph)
