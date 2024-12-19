"""
Story Graph Module
Handles game workflow and state transitions.
"""

from typing import Dict, Optional, AsyncGenerator, Any, Union
from pydantic import BaseModel, ConfigDict, Field
from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from agents.narrator_agent import NarratorAgent
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.trace_agent import TraceAgent
from managers.state_manager import StateManager
from managers.trace_manager import TraceManager
from config.agents.base import AgentConfig
from config.logging_config import get_logger
from agents.protocols import StoryGraphProtocol

# Import GameState en dehors de TYPE_CHECKING car on en a besoin pour l'exécution
from models.game_state import GameState


logger = get_logger('story_graph')

class StoryGraph(BaseAgent, StoryGraphProtocol):
    """Manages the game workflow and state transitions."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: AgentConfig
    state_manager: StateManager
    _graph: Optional[StateGraph] = None
    _current_section: int = 1

    def __init__(
        self,
        config: AgentConfig,
        narrator_agent: NarratorAgent,
        rules_agent: RulesAgent,
        decision_agent: DecisionAgent,
        trace_agent: TraceAgent,
        state_manager: StateManager
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
        super().__init__(config)
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
            return self.state_manager.create_error_state(str(e))

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
            rules = await self.rules_agent.analyze_rules(
                from_state.section_number,
                from_state.narrative.content if from_state.narrative else ""
            )
            
            # Check if transition is allowed
            return to_state.section_number in rules.next_sections
        except Exception as e:
            logger.error(f"Error validating state transition: {e}")
            return False

    async def process_game_section(self, section_number: int) -> GameState:
        """
        Process a complete game section.
        
        Args:
            section_number: Section to process
            
        Returns:
            GameState: Processed game state
        """
        try:
            # Read section content
            narrative = await self.narrator_agent.read_section(section_number)
            
            # Process rules
            rules = await self.rules_agent.analyze_rules(
                section_number,
                narrative.content if narrative else ""
            )
            
            # Create initial state
            state = GameState(
                section_number=section_number,
                narrative=narrative,
                rules=rules
            )
            
            # Execute workflow
            return await self.execute_game_workflow(state)
        except Exception as e:
            logger.error(f"Error processing game section: {e}")
            return self.state_manager.create_error_state(str(e))

    async def apply_section_rules(self, state: GameState) -> GameState:
        """
        Apply game rules to the current state.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: State with rules applied
        """
        try:
            # Process rules
            rules = await self.rules_agent.analyze_rules(
                state.section_number,
                state.narrative.content if state.narrative else ""
            )
            
            # Update state with rules
            state.rules = rules
            return state
        except Exception as e:
            logger.error(f"Error applying section rules: {e}")
            return self.state_manager.create_error_state(str(e))

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
            
            return GameState(
                section_number=narrative.section_number if narrative else self._current_section,
                narrative=narrative,
                rules=rules,
                decision=decision,
                trace=trace
            )
        except Exception as e:
            logger.error(f"Error merging agent results: {e}")
            return self.state_manager.create_error_state(str(e))

    async def start_session(self) -> None:
        """Démarre une nouvelle session de jeu."""
        try:
            logger.info("Starting story graph session...")
            
            # Configurer le workflow
            await self._setup_workflow()
            
            # Démarrer le workflow avec un état vide
            # Le noeud start se chargera de l'initialisation
            await self._process_workflow({})
            
            logger.info("Story graph session started successfully")
        except Exception as e:
            logger.error(f"Failed to start story graph session: {e}")
            raise

    async def _setup_workflow(self) -> None:
        """Configure le workflow langgraph."""
        try:
            # Créer le graph
            self._graph = StateGraph()
            
            # Ajouter les noeuds
            self._graph.add_node("start", self._initialize_state)
            self._graph.add_node("narrator", self._process_narrative)
            self._graph.add_node("rules", self._process_rules)
            self._graph.add_node("decision", self._process_decision)
            self._graph.add_node("trace", self._process_trace)
            
            # Définir le flux
            self._graph.add_edge("start", "narrator")
            self._graph.add_edge("narrator", "rules")
            self._graph.add_edge("rules", "decision")
            self._graph.add_edge("decision", "trace")
            self._graph.add_edge("trace", END)
            
            # Compiler
            self._graph.compile()
            
        except Exception as e:
            logger.error(f"Error setting up workflow: {e}")
            raise
            
    async def _initialize_state(self, state: Dict) -> Dict:
        """Noeud d'initialisation dans le workflow."""
        try:
            # Créer l'état initial si nécessaire
            if not state:
                state = await self.state_manager.create_initial_state()
                state = state.model_dump()
            
            # S'assurer que les champs requis sont présents
            state.setdefault('section_number', self._current_section)
            state.setdefault('content', None)
            state.setdefault('rules', None)
            state.setdefault('decision', None)
            state.setdefault('trace', None)
            
            return state
            
        except Exception as e:
            logger.error(f"Error initializing state: {e}")
            raise

    async def _process_workflow(self, state: Dict, stream: bool = False) -> Union[Dict, AsyncGenerator[Dict, None]]:
        """Process the workflow with optional streaming."""
        try:
            if stream:
                async for step_state in self._graph.astream(state):
                    # Mise à jour du state manager à chaque étape
                    await self.state_manager.update_state(step_state)
                    yield step_state
            else:
                final_state = await self._graph.arun(state)
                await self.state_manager.update_state(final_state)
                return final_state
                
        except Exception as e:
            logger.error(f"Error in workflow processing: {e}")
            error_state = await self.state_manager.create_error_state(str(e))
            return error_state

    async def stream_game_state(self) -> AsyncGenerator[Dict, None]:
        """Stream l'état du jeu à chaque étape du workflow."""
        try:
            # Démarrer avec un état vide, le noeud start l'initialisera
            async for state in self._process_workflow({}, stream=True):
                yield state
        except Exception as e:
            logger.error(f"Error streaming game state: {e}")
            yield await self.state_manager.create_error_state(str(e))

    async def _process_narrative(self, state: Dict) -> Dict:
        """Process narrative node in workflow."""
        try:
            return await self.narrator_agent.process_section(state)
        except Exception as e:
            logger.error(f"Error in narrative processing: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def _process_rules(self, state: Dict) -> Dict:
        """Process rules node in workflow."""
        try:
            return await self.rules_agent.analyze_rules(state)
        except Exception as e:
            logger.error(f"Error in rules processing: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def _process_decision(self, state: Dict) -> Dict:
        """Process decision node in workflow."""
        try:
            return await self.decision_agent.process_decision(state)
        except Exception as e:
            logger.error(f"Error in decision processing: {e}")
            return await self.state_manager.create_error_state(str(e))

    async def _process_trace(self, state: Dict) -> Dict:
        """Process trace node in workflow."""
        try:
            return await self.trace_agent.record_state(state)
        except Exception as e:
            logger.error(f"Error in trace processing: {e}")
            return await self.state_manager.create_error_state(str(e))
