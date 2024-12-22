"""
Agent responsable des décisions.
"""
from typing import Dict, Optional, Any, List, AsyncGenerator, Union
import json
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, model_validator, ConfigDict
from models.game_state import GameState
from models.decision_model import DecisionModel, AnalysisResult
from models.rules_model import RulesModel
from models.errors_model import DecisionError
from langchain_core.messages import HumanMessage, SystemMessage
from agents.rules_agent import RulesAgent
from agents.base_agent import BaseAgent
from config.agents.decision_agent_config import DecisionAgentConfig as DecisionConfig
from config.logging_config import get_logger
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol
from agents.protocols import DecisionAgentProtocol

# Type pour les agents de règles (réel ou mock)
RulesAgentType = Union[RulesAgent, Any]

class DecisionAgent(BaseAgent, DecisionAgentProtocol):
    """Agent responsable des décisions."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, config: DecisionConfig, decision_manager: DecisionManagerProtocol):
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
        self._logger = get_logger("decision_agent")
        
        if self.config.debug:
            self._logger.setLevel("DEBUG")

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
                return AnalysisResult(
                    next_section=result.get("next_section"),
                    conditions=result.get("conditions", []),
                    analysis=result.get("analysis", "")
                )
                
            except json.JSONDecodeError:
                raise DecisionError("Invalid LLM response format")

        except Exception as e:
            self._logger.error(f"Error analyzing response: {e}")
            raise DecisionError(f"Failed to analyze response: {str(e)}")

    async def analyze_decision(self, state: GameState) -> GameState:
        """
        Analyze user decisions and validate against rules.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: Updated game state with decision analysis
        """
        try:
            section_number = state.section_number
            player_input = state.player_input
            dice_roll = state.dice_roll
            rules = state.rules

            if not rules:
                return GameState(
                    section_number=section_number,
                    error="Règles non trouvées pour la section {section_number}"
                )

            # Vérifier si on a besoin d'un jet de dés
            needs_dice = rules.needs_dice
            next_action = rules.next_action  # Optionnel: force l'ordre ("user_first", "dice_first")

            # Si un ordre est spécifié
            if next_action == "user_first" and not player_input:
                return GameState(
                    section_number=section_number,
                    narrative=state.narrative,
                    rules=rules,
                    awaiting_action="user_response",
                    choices=rules.choices,
                    analysis="En attente de la réponse de l'utilisateur"
                )
            elif next_action == "dice_first" and not dice_roll:
                return GameState(
                    section_number=section_number,
                    narrative=state.narrative,
                    rules=rules,
                    awaiting_action="dice_roll",
                    dice_type=rules.dice_type,
                    analysis="En attente du jet de dés"
                )

            # Sinon vérifier ce qui manque
            # Vérifier d'abord les dés car c'est plus prioritaire
            if needs_dice and not dice_roll:
                return GameState(
                    section_number=section_number,
                    narrative=state.narrative,
                    rules=rules,
                    awaiting_action="dice_roll",
                    dice_type=rules.dice_type,
                    analysis="En attente du jet de dés"
                )

            # Ensuite vérifier la réponse utilisateur
            needs_user_response = rules.needs_user_response
            if needs_user_response and not player_input:
                return GameState(
                    section_number=section_number,
                    narrative=state.narrative,
                    rules=rules,
                    awaiting_action="user_response",
                    choices=rules.choices,
                    analysis="En attente de la réponse de l'utilisateur"
                )

            # Formater la réponse
            formatted_response = self.decision_manager.format_response(player_input, dice_roll.value if dice_roll else None)

            # Analyser la réponse
            analysis_result = await self.analyze_response(
                section_number,
                formatted_response,
                rules.model_dump()
            )

            # Construire la décision finale
            decision = DecisionModel(
                section_number=analysis_result.next_section,
                awaiting_action=None,
                conditions=analysis_result.conditions
            )

            return GameState(
                section_number=section_number,
                narrative=state.narrative,
                rules=rules,
                decision=decision,
                trace=state.trace,
                analysis=analysis_result.analysis
            )

        except Exception as e:
            self._logger.error(f"Error in analyze_decision: {str(e)}")
            return GameState(
                section_number=state.section_number,
                error=str(e)
            )

    async def invoke(self, input_data: Dict) -> Dict[str, GameState]:
        """
        Méthode principale appelée par le graph.
        
        Args:
            input_data (Dict): Dictionnaire contenant le state
            
        Returns:
            Dict[str, GameState]: État mis à jour avec la décision validée
        """
        try:
            # Validation de l'état d'entrée avec Pydantic
            if not isinstance(input_data.get("state"), GameState):
                state = GameState.model_validate(input_data.get("state", {}))
            else:
                state = input_data["state"]

            if not state.section_number:
                return {
                    "state": GameState(
                        section_number=1,
                        error="Section number required"
                    )
                }

            # Obtention des règles via RulesAgent si nécessaire
            if not state.rules and self.rules_agent:
                rules_result = await self.rules_agent.invoke({
                    "state": GameState(
                        section_number=state.section_number,
                        narrative=state.narrative
                    ).model_dump()
                })
                
                if isinstance(rules_result.get("state"), dict):
                    rules = RulesModel.model_validate(rules_result["state"].get("rules", {}))
                    state.rules = rules

            # Analyse de la décision
            analysis_result = await self.analyze_decision(state)
            
            # Construction et validation de la décision
            if analysis_result.get("decision"):
                decision = analysis_result.decision
                
                # Mise à jour de l'état avec la nouvelle décision
                updated_state = GameState(
                    section_number=state.section_number,
                    narrative=state.narrative,
                    rules=state.rules,
                    trace=state.trace,
                    character=state.character,
                    dice_roll=state.dice_roll,
                    decision=decision,
                    player_input=state.player_input
                )
                
                if self.config.debug:
                    self._logger.debug(f"Decision made: {decision.model_dump_json(indent=2)}")
                
                return {"state": updated_state}
            
            # En cas d'erreur d'analyse
            return {
                "state": GameState(
                    section_number=state.section_number,
                    error="Could not determine next section"
                )
            }

        except Exception as e:
            self._logger.error(f"Error in DecisionAgent.invoke: {str(e)}")
            return {
                "state": GameState(
                    section_number=state.section_number if state else 1,
                    error=str(e)
                )
            }

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """Méthode pour l'interface asynchrone."""
        try:
            state = GameState.model_validate(input_data.get("state", {}))
            analysis_result = await self.analyze_decision(state)
            
            if analysis_result.get("decision"):
                decision = analysis_result.decision
                
                # Mise à jour de l'état avec la nouvelle décision
                updated_state = GameState(
                    section_number=state.section_number,
                    narrative=state.narrative,
                    rules=state.rules,
                    trace=state.trace,
                    character=state.character,
                    dice_roll=state.dice_roll,
                    decision=decision,
                    player_input=state.player_input
                )
                
                if self.config.debug:
                    self._logger.debug(f"Decision made: {decision.model_dump_json(indent=2)}")
                
                yield {"state": updated_state.model_dump()}
            else:
                yield {"error": "No valid next section found"}
            
        except Exception as e:
            self._logger.error(f"[DecisionAgent] Error during invocation: {e}")
            yield {"error": f"Error during invocation: {str(e)}"}
