from typing import Dict, Optional, Any, List, AsyncGenerator, Union
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, ConfigDict, Field
from agents.models import GameState
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from agents.rules_agent import RulesAgent
import logging
import json
from agents.base_agent import BaseAgent

# Type pour les agents de règles (réel ou mock)
RulesAgentType = Union[RulesAgent, Any]

class DecisionConfig(BaseModel):
    """Configuration pour DecisionAgent."""
    llm: Optional[BaseChatModel] = Field(default_factory=lambda: ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        model_kwargs={
            "system_message": """Tu es un agent de décision pour un livre-jeu.
            Tu dois analyser les réponses du joueur et déterminer les actions à effectuer."""
        }
    ))
    rules_agent: Optional[RulesAgentType] = None
    system_prompt: str = Field(default="""Tu es un agent qui analyse les réponses de l'utilisateur.
Détermine la prochaine section en fonction de la réponse.""")
    model_config = ConfigDict(arbitrary_types_allowed=True)

class DecisionAgent(BaseAgent):
    """
    Agent responsable des décisions.
    """
    
    def __init__(self, config: Optional[DecisionConfig] = None, event_bus: Optional[Any] = None, **kwargs):
        """
        Initialise l'agent avec une configuration Pydantic.
        
        Args:
            config: Configuration Pydantic (optionnel)
            event_bus: Bus d'événements pour la communication entre agents
            **kwargs: Arguments supplémentaires pour la configuration
        """
        super().__init__(event_bus=event_bus)  # Appel au constructeur parent avec event_bus
        self.config = config or DecisionConfig(**kwargs)
        self.llm = self.config.llm
        self.rules_agent = self.config.rules_agent
        self.system_prompt = self.config.system_prompt
        self.cache = {}
        self._logger: logging.Logger

    async def invoke(self, input_data: Dict) -> Dict:
        """
        Méthode principale appelée par le graph.
        
        Args:
            input_data (Dict): Dictionnaire contenant le state avec section_number, user_response, rules, etc.
            
        Returns:
            Dict: État mis à jour avec la décision
        """
        try:
            state = input_data.get("state", {})
            if isinstance(state, GameState):
                state = state.dict()
            
            section_number = state.get("section_number")
            user_response = state.get("user_response")
            rules = state.get("rules", {})

            if not section_number:
                return {
                    "state": {
                        "error": "Section number required",
                        "awaiting_action": None,
                        "analysis": None
                    }
                }

            # Si les règles ne sont pas dans le state, les demander au RulesAgent
            if not rules and self.rules_agent:
                rules_result = await self.rules_agent.invoke({
                    "state": {
                        "section_number": section_number,
                        "current_section": state.get("current_section", {})
                    }
                })
                rules = rules_result.get("state", {}).get("rules", {})
                state["rules"] = rules

            return await self._analyze_decision(state)

        except Exception as e:
            self._logger.error(f"Error in DecisionAgent.invoke: {str(e)}")
            return {"state": {"error": str(e)}}

    async def ainvoke(
        self, input_data: Dict, config: Optional[Dict] = None
    ) -> Dict:
        """Version asynchrone de invoke."""
        return await self.invoke(input_data)

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

    async def _analyze_decision(self, state: Dict) -> Dict:
        """
        Analyse la décision en fonction de l'état.
        
        Args:
            state: État actuel
        
        Returns:
            Dict: Décision
        """
        try:
            section_number = state.get("section_number")
            user_response = state.get("user_response")
            dice_result = state.get("dice_result")
            rules = state.get("rules", {})

            if not rules:
                return {"state": {"error": f"Règles non trouvées pour la section {section_number}"}}

            # Vérifier si on a besoin d'un jet de dés
            needs_dice = rules.get("needs_dice", False)
            next_action = rules.get("next_action")  # Optionnel: force l'ordre ("user_first", "dice_first")

            # Si un ordre est spécifié
            if next_action == "user_first" and not user_response:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "user_response",
                    "choices": rules.get("choices", []),
                    "analysis": "En attente de la réponse de l'utilisateur"
                })
                return {"state": updated_state}
            elif next_action == "dice_first" and not dice_result:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                })
                return {"state": updated_state}

            # Sinon vérifier ce qui manque
            # Vérifier d'abord les dés car c'est plus prioritaire
            if needs_dice and not dice_result:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "dice_roll",
                    "dice_type": rules.get("dice_type", "normal"),
                    "analysis": "En attente du jet de dés"
                })
                return {"state": updated_state}

            # Ensuite vérifier la réponse utilisateur
            needs_user_response = rules.get("needs_user_response", True)
            if needs_user_response and not user_response:
                updated_state = state.copy()
                updated_state.update({
                    "section_number": section_number,
                    "awaiting_action": "user_response",
                    "choices": rules.get("choices", []),
                    "analysis": "En attente de la réponse de l'utilisateur"
                })
                return {"state": updated_state}

            # Si on a tout ce dont on a besoin, analyser avec le LLM
            analysis_result = await self._analyze_response(
                section_number, 
                self._format_response(user_response, dice_result),
                rules
            )

            updated_state = state.copy()
            updated_state.update({
                "next_section": analysis_result.get("next_section"),
                "analysis": analysis_result["analysis"],
                "awaiting_action": None
            })
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
