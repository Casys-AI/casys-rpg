"""
Agent responsable des décisions.
"""
from typing import Dict, Optional, Any, List, AsyncGenerator, Union
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, model_validator, ConfigDict
from models.game_state import GameState
from models.decision_model import DecisionModel
from models.rules_model import RulesModel
from models.narrator_model import NarratorModel
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from agents.rules_agent import RulesAgent
from agents.base_agent import BaseAgent
from config.agent_config import DecisionConfig
from config.logging_config import get_logger
from managers.cache_manager import CacheManager
from agents.protocols import DecisionAgentProtocol
import json

# Type pour les agents de règles (réel ou mock)
RulesAgentType = Union[RulesAgent, Any]

class DecisionAgent(BaseAgent, DecisionAgentProtocol):
    """Agent responsable des décisions."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, config: DecisionConfig, cache_manager: CacheManager):
        """
        Initialise l'agent avec une configuration.
        
        Args:
            config: Configuration de l'agent
            cache_manager: Gestionnaire de cache
        """
        super().__init__(config=config, cache_manager=cache_manager)
        self.llm = self.config.llm
        self.rules_agent = self.config.dependencies.get("rules_agent")
        self.system_prompt = self.config.system_message
        self.cache = {} if self.config.cache_enabled else None
        self._logger = get_logger("decision_agent")
        
        if self.config.debug:
            self._logger.setLevel("DEBUG")

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
            analysis_result = await self._analyze_decision(state)
            
            # Construction et validation de la décision
            if analysis_result.get("next_section"):
                decision = DecisionModel(
                    section_number=analysis_result["next_section"],
                    awaiting_action=analysis_result.get("needs_action", False),
                    conditions=analysis_result.get("conditions", [])
                )
                
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
            analysis_result = await self._analyze_decision(state)
            
            if analysis_result.get("next_section"):
                decision = DecisionModel(
                    section_number=analysis_result["next_section"],
                    awaiting_action=analysis_result.get("needs_action", False),
                    conditions=analysis_result.get("conditions", [])
                )
                
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

    async def _analyze_response(self, section_number: int, user_response: str, rules: Dict = None) -> Dict:
        """
        Analyse la réponse de l'utilisateur avec le LLM en tenant compte des règles.
        
        Args:
            section_number: Numéro de la section actuelle
            user_response: Réponse de l'utilisateur ou résultat des dés
            rules: Règles à appliquer pour l'analyse
            
        Returns:
            Dict: Résultat de l'analyse avec next_section et analysis
        """
        try:
            if user_response is None:
                return {
                    "analysis": "Pas de réponse à analyser",
                    "next_section": None
                }
            
            # Construction du contexte pour le LLM
            context = (
                "En tant qu'agent de décision pour un livre-jeu, analyse la réponse de l'utilisateur "
                "et détermine la prochaine section en fonction des règles.\n\n"
                f"Section actuelle: {section_number}\n"
                f"Réponse/Action: {user_response}\n"
            )
            
            if rules:
                context += "\nRègles et conditions:\n"
                if "conditions" in rules:
                    context += "- Conditions: " + ", ".join(rules["conditions"]) + "\n"
                if "choices" in rules:
                    context += "- Choix possibles:\n"
                    for i, choice in enumerate(rules["choices"], 1):
                        context += f"  {i}. {choice}\n"
                if "next_sections" in rules:
                    context += "- Sections possibles: " + ", ".join(map(str, rules["next_sections"])) + "\n"
                if "rules_summary" in rules:
                    context += f"\nRésumé des règles: {rules['rules_summary']}\n"
            
            context += "\nAnalyse la réponse et retourne:\n"
            context += "1. Une analyse détaillée de la décision\n"
            context += "2. La prochaine section à suivre\n"
            context += "Format: JSON avec 'analysis' et 'next_section'\n"
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=context)
            ]
            
            response = await self.llm.ainvoke(messages)
            try:
                # Tenter de parser la réponse JSON
                result = json.loads(response.content)
                if not isinstance(result, dict):
                    raise ValueError("La réponse n'est pas un dictionnaire")
                if "analysis" not in result or "next_section" not in result:
                    raise ValueError("La réponse ne contient pas les champs requis")
                return result
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON, essayer d'extraire les informations
                content = response.content.strip()
                # Demander au LLM de reformater sa réponse en JSON
                format_context = (
                    "Reformate ta réponse précédente en JSON avec les champs 'analysis' et 'next_section':\n\n"
                    f"Réponse à formater: {content}"
                )
                format_messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=format_context)
                ]
                format_response = await self.llm.ainvoke(format_messages)
                try:
                    result = json.loads(format_response.content)
                    if "analysis" not in result or "next_section" not in result:
                        raise ValueError
                    return result
                except (json.JSONDecodeError, ValueError):
                    return {
                        "analysis": content,
                        "next_section": None
                    }
            
        except Exception as e:
            self._logger.error(f"Error analyzing response: {str(e)}")
            return {
                "analysis": f"Error analyzing response: {str(e)}",
                "next_section": None
            }

    async def _analyze_decision(self, state: GameState) -> Dict:
        """
        Analyse la décision en fonction de l'état.
        
        Args:
            state: État actuel
        
        Returns:
            Dict: Décision
        """
        try:
            section_number = state.section_number
            player_input = state.player_input
            dice_roll = state.dice_roll
            rules = state.rules

            if not rules:
                return {"state": {"error": f"Règles non trouvées pour la section {section_number}"}}

            # Vérifier si on a besoin d'un jet de dés
            needs_dice = rules.needs_dice
            next_action = rules.next_action  # Optionnel: force l'ordre ("user_first", "dice_first")

            # Si un ordre est spécifié
            if next_action == "user_first" and not player_input:
                updated_state = state.model_copy()
                updated_state.section_number = section_number
                updated_state.awaiting_action = "user_response"
                updated_state.choices = rules.choices
                updated_state.analysis = "En attente de la réponse de l'utilisateur"
                return {"state": updated_state}
            elif next_action == "dice_first" and not dice_roll:
                updated_state = state.model_copy()
                updated_state.section_number = section_number
                updated_state.awaiting_action = "dice_roll"
                updated_state.dice_type = rules.dice_type
                updated_state.analysis = "En attente du jet de dés"
                return {"state": updated_state}

            # Sinon vérifier ce qui manque
            # Vérifier d'abord les dés car c'est plus prioritaire
            if needs_dice and not dice_roll:
                updated_state = state.model_copy()
                updated_state.section_number = section_number
                updated_state.awaiting_action = "dice_roll"
                updated_state.dice_type = rules.dice_type
                updated_state.analysis = "En attente du jet de dés"
                return {"state": updated_state}

            # Ensuite vérifier la réponse utilisateur
            needs_user_response = rules.needs_user_response
            if needs_user_response and not player_input:
                updated_state = state.model_copy()
                updated_state.section_number = section_number
                updated_state.awaiting_action = "user_response"
                updated_state.choices = rules.choices
                updated_state.analysis = "En attente de la réponse de l'utilisateur"
                return {"state": updated_state}

            # Si on a tout ce dont on a besoin, analyser avec le LLM
            analysis_result = await self._analyze_response(
                section_number, 
                self._format_response(player_input, dice_roll),
                rules.model_dump()
            )

            updated_state = state.model_copy()
            updated_state.next_section = analysis_result.get("next_section")
            updated_state.analysis = analysis_result["analysis"]
            updated_state.awaiting_action = None
            return {"state": updated_state}

        except Exception as e:
            self._logger.error(f"Error in _analyze_decision: {str(e)}")
            return {"state": state}

    def _format_response(self, user_response: Optional[str], dice_result: Optional[int]) -> str:
        """
        Formate la réponse complète avec le résultat du dé si présent.
        """
        if user_response and dice_result:
            return f"{user_response} (Dé: {dice_result})"
        elif user_response:
            return user_response
        elif dice_result:
            return f"Résultat du dé: {dice_result}"
        return ""
