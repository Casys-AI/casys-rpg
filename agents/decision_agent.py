"""
Agent responsable des décisions.
"""
from typing import Dict, Optional, Any, List, AsyncGenerator, Union
from langchain.schema.runnable import RunnableSerializable
from pydantic import Field
from models.game_state import GameState
from models.decision_model import DecisionModel, AnalysisResult
from models.rules_model import RulesModel
from models.errors_model import DecisionError
from langchain_core.messages import HumanMessage, SystemMessage
from agents.base_agent import BaseAgent
from config.agents.decision_agent_config import DecisionAgentConfig
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from agents.protocols import DecisionAgentProtocol
from agents.protocols.rules_agent_protocol import RulesAgentProtocol
from datetime import datetime
from loguru import logger
import json

# Type pour les agents de règles (réel ou mock)
RulesAgentType = Union[RulesAgentProtocol, Any]

class DecisionAgent(BaseAgent):
    """Agent responsable des décisions."""
    
    config: DecisionAgentConfig = Field(default_factory=DecisionAgentConfig)
    
    def __init__(self, config: DecisionAgentConfig, decision_manager: DecisionManagerProtocol):
        """
        Initialise l'agent avec une configuration.
        
        Args:
            config: Configuration de l'agent
            decision_manager: Manager pour les décisions
        """
        super().__init__(config=config)
        self.decision_manager = decision_manager
        self.rules_agent = self.config.dependencies.get("rules_agent")
        self.llm = self.config.llm
        self.system_prompt = self.config.system_message
        self._logger = logger

    async def analyze_response(
        self,
        section_number: int,
        user_response: str,
        rules: Dict
    ) -> AnalysisResult:
        """
        Analyse la réponse avec le LLM.
        
        Args:
            section_number: Section actuelle
            user_response: Réponse utilisateur ou résultat des dés
            rules: Règles à appliquer
            
        Returns:
            AnalysisResult: Résultat de l'analyse
        """
        try:
            # Construire le prompt
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
                    Section actuelle: {section_number}
                    Réponse utilisateur: {user_response}
                    Règles: {json.dumps(rules, indent=2)}
                """)
            ]
            
            # Appeler le LLM
            response = await self.llm.ainvoke(messages)
            
            # Parser la réponse
            try:
                result = json.loads(response.content)
                next_section = result.get("next_section")
                if next_section is None:
                    raise DecisionError("Missing next_section in LLM response")
                    
                return AnalysisResult(
                    next_section=next_section,
                    conditions=result.get("conditions", []),
                    analysis=result.get("analysis", "")
                )
                
            except json.JSONDecodeError:
                raise DecisionError("Invalid LLM response format")

        except Exception as e:
            self._logger.error(f"Error analyzing response: {e}")
            raise DecisionError(f"Failed to analyze response: {str(e)}")

    async def _process_decision(
        self,
        player_input: str,
        rules: RulesModel,
        section_number: int
    ) -> Union[DecisionModel, DecisionError]:
        """Process a player decision."""
        try:
            self._logger.info("Processing decision for section {} with input: {}", section_number, player_input)
            
            if not rules:
                self._logger.error("No rules found for section {}", section_number)
                return DecisionModel(
                    section_number=section_number,
                    error=f"Règles non trouvées pour la section {section_number}"
                )

            # Vérifier si on a besoin d'un jet de dés
            needs_dice = rules.needs_dice
            next_action = rules.next_action
            self._logger.debug("Rules state: needs_dice={}, next_action={}", needs_dice, next_action)

            # Si un ordre est spécifié
            if next_action == "user_first" and not player_input:
                self._logger.info("Waiting for user input first")
                return DecisionModel(
                    section_number=section_number,
                    awaiting_action="user_response",
                    choices=rules.choices,
                    analysis="En attente de la réponse de l'utilisateur"
                )
            elif next_action == "dice_first":
                self._logger.info("Waiting for dice roll first")
                return DecisionModel(
                    section_number=section_number,
                    awaiting_action="dice_roll",
                    dice_type=rules.dice_type,
                    analysis="En attente du jet de dés"
                )

            # Sinon vérifier ce qui manque
            if needs_dice:
                self._logger.info("Dice roll needed")
                return DecisionModel(
                    section_number=section_number,
                    awaiting_action="dice_roll",
                    dice_type=rules.dice_type,
                    analysis="En attente du jet de dés"
                )

            # Analyser la réponse utilisateur
            self._logger.info("Analyzing user response")
            analysis_result = await self.analyze_response(
                section_number,
                player_input,
                rules.model_dump()
            )

            self._logger.info("Analysis complete: current_section={}, next_section={}", 
                          section_number, analysis_result.next_section)

            return DecisionModel(
                section_number=section_number,
                next_section=analysis_result.next_section,
                analysis=analysis_result.analysis,
                error=analysis_result.error
            )

        except Exception as e:
            self._logger.exception("Error in decision processing: {}", str(e))
            return DecisionError(str(e))

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict[str, Any], None]:
        """Async invocation for decision processing."""
        try:
            state = GameState.model_validate(input_data.get("state", {}))
            self._logger.info("Starting decision processing: session={}, section={}, input={}", 
                         state.session_id, state.section_number, state.player_input)
            
            # Process decision
            decision = await self._process_decision(
                state.player_input,
                state.rules,
                state.section_number
            )
            
            if isinstance(decision, DecisionError):
                self._logger.error("Decision processing error: {}", decision.message)
                error_decision = DecisionModel(
                    section_number=state.section_number,
                    next_section=state.section_number,  
                    error=decision.message,
                    timestamp=datetime.now()
                )
                yield {"decision": error_decision}
            else:
                self._logger.info("Decision processed successfully: next_section={}", 
                             getattr(decision, 'next_section', None))
                yield {"decision": decision}
                
        except Exception as e:
            self._logger.exception("Error in ainvoke: {}", str(e))
            error_decision = DecisionModel(
                section_number=state.section_number,
                next_section=state.section_number,  
                error=str(e),
                timestamp=datetime.now()
            )
            yield {"decision": error_decision}


DecisionAgentProtocol.register(DecisionAgent)
