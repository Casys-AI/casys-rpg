from typing import Optional, Dict, List, AsyncGenerator
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from agents.base_agent import BaseAgent
from event_bus import Event, EventBus
from agents.models import GameState
import os
import json
import logging
import re

logger = logging.getLogger(__name__)

class RuleAnalysis(BaseModel):
    """Structure pour l'analyse des règles d'une section."""
    needs_dice: bool = Field(default=False, description="Si un lancer de dés est nécessaire")
    dice_type: Optional[str] = Field(default=None, description="Type de dé requis (combat/chance)")
    next_sections: List[int] = Field(default_factory=list, description="Liste des sections suivantes possibles")
    conditions: List[str] = Field(default_factory=list, description="Liste des conditions à remplir")
    choices: List[str] = Field(default_factory=list, description="Liste des choix possibles")
    rules_summary: Optional[str] = Field(default=None, description="Résumé des règles en une phrase")
    error: Optional[str] = Field(default=None, description="Message d'erreur si présent")
    source: Optional[str] = Field(default=None, description="Source des règles (cache/analysis/error)")
    raw_content: Optional[str] = Field(default=None, description="Contenu brut de la section")

class RulesConfig(BaseModel):
    """Configuration pour RulesAgent."""
    llm: Optional[BaseChatModel] = Field(
        default_factory=lambda: ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        ),
        description="Modèle de langage à utiliser"
    )
    rules_directory: str = Field(
        default="data/rules",
        description="Répertoire contenant les règles"
    )
    system_prompt: SystemMessage = Field(
        default_factory=lambda: SystemMessage(
            content="""Tu es un expert en analyse de règles de jeu.

"""
        )
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)

class RulesAgent(BaseAgent):
    """Agent responsable de l'analyse des règles."""

    def __init__(self, event_bus: Optional[EventBus] = None, config: Optional[RulesConfig] = None, **kwargs):
        """
        Initialise l'agent des règles.
        
        Args:
            event_bus (Optional[EventBus]): Bus d'événements pour la communication
            config (Optional[RulesConfig]): Configuration de l'agent
            **kwargs: Arguments supplémentaires pour la configuration
        """
        super().__init__(event_bus)
        self.config = config or RulesConfig(**kwargs)
        self.llm = self.config.llm
        self.rules_directory = self.config.rules_directory
        self.cache_dir = os.path.join("data", "rules", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.parser = PydanticOutputParser(pydantic_object=RuleAnalysis)

    def _get_cache_path(self, section_number: int) -> str:
        """Retourne le chemin du fichier de cache pour une section."""
        return os.path.join(self.cache_dir, f"section_{section_number}_rules.json")

    def _load_from_cache(self, section_number: int) -> Optional[Dict]:
        """Charge les règles depuis le cache."""
        cache_path = self._get_cache_path(section_number)
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                    rules["source"] = "cache"
                    return rules
        except Exception as e:
            logger.error(f"Error loading cache for section {section_number}: {str(e)}")
        return None

    def _save_to_cache(self, section_number: int, rules: Dict) -> None:
        """Sauvegarde les règles dans le cache."""
        cache_path = self._get_cache_path(section_number)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache for section {section_number}: {str(e)}")

    async def invoke(self, input_data: Dict) -> Dict:
        """
        Analyse les règles pour une section donnée.
        
        Args:
            input_data (Dict): Données d'entrée avec l'état du jeu
            
        Returns:
            Dict: État mis à jour avec les règles analysées
        """
        try:
            state = input_data.get("state", {})
            section_number = state.get("section_number", None)
            
            logger.debug(f"Processing section {section_number}")
            
            if section_number is None or section_number < 1:
                error_state = {
                    "error": "Invalid section number",
                    "needs_dice": False,
                    "dice_type": None,
                    "conditions": [],
                    "next_sections": [],
                    "rules_summary": None,
                    "raw_content": "",
                    "choices": [],
                    "source": "error"
                }
                return {"state": {"section_number": section_number, "current_section": {}, "rules": error_state}}

            # Extraire le contenu
            current_section = state.get("current_section", {})
            raw_content = current_section.get("raw_content", current_section.get("content", ""))
            logger.debug(f"Raw content: {raw_content}")

            # Vérification directe des mots-clés
            dice_keywords = ["jet de dés", "lancer les dés", "faire un jet"]
            combat_keywords = ["combat", "affronter", "battre", "vaincre", "habileté", "endurance"]
            chance_keywords = ["chance", "tentez votre chance", "test de chance"]

            has_dice = any(keyword in raw_content.lower() for keyword in dice_keywords)
            has_combat = any(keyword in raw_content.lower() for keyword in combat_keywords)
            has_chance = any(keyword in raw_content.lower() for keyword in chance_keywords)

            logger.debug(f"Keyword detection: dice={has_dice}, combat={has_combat}, chance={has_chance}")

            # Vérifier le cache
            cached_rules = self._load_from_cache(section_number)
            if cached_rules:
                logger.debug(f"Cache hit for section {section_number}")
                rules = dict(cached_rules)
                if has_dice or has_combat or has_chance:
                    rules["needs_dice"] = True
                    if has_combat:
                        rules["dice_type"] = "combat"
                    elif has_chance:
                        rules["dice_type"] = "chance"
                rules["raw_content"] = raw_content
                state["rules"] = rules
                return {"state": state}

            # Charger les règles du fichier si disponible
            rules_content = await self._load_rules_file(section_number)
            if rules_content:
                logger.debug(f"Using rules file for section {section_number}")
                content_to_analyze = rules_content
            else:
                content_to_analyze = raw_content

            # Analyser les règles
            rules = await self._analyze_rules(section_number, content_to_analyze)
            if rules:
                # Forcer les règles basées sur les mots-clés
                if has_dice or has_combat or has_chance:
                    rules["needs_dice"] = True
                    if has_combat:
                        rules["dice_type"] = "combat"
                    elif has_chance:
                        rules["dice_type"] = "chance"
                    logger.debug(f"Forced dice rules: needs_dice={rules['needs_dice']}, dice_type={rules['dice_type']}")

                rules["raw_content"] = raw_content
                rules["source"] = "analysis"
                self._save_to_cache(section_number, rules)
                
                if self.event_bus:
                    await self.event_bus.emit(
                        Event(type="rules_generated", data={
                            "section_number": section_number,
                            "rules": rules
                        })
                    )
            else:
                rules = {
                    "error": f"Failed to analyze rules for section {section_number}",
                    "choices": [],
                    "needs_dice": has_dice or has_combat or has_chance,
                    "dice_type": "combat" if has_combat else ("chance" if has_chance else None),
                    "source": "error",
                    "raw_content": raw_content,
                    "next_sections": [],
                    "conditions": []
                }

            state["rules"] = rules
            return {"state": state}

        except Exception as e:
            logger.error(f"Error in RulesAgent.invoke: {str(e)}")
            return {
                "state": {
                    "error": str(e),
                    "choices": [],
                    "needs_dice": False,
                    "dice_type": None,
                    "source": "error",
                    "raw_content": "",
                    "next_sections": [],
                    "conditions": []
                }
            }

    async def _analyze_rules(self, section_number: int, content: str) -> Optional[Dict]:
        """
        Analyse les règles pour une section donnée avec le LLM.
        
        Args:
            section_number (int): Numéro de la section
            content (str): Contenu à analyser
            
        Returns:
            Optional[Dict]: Règles analysées ou None en cas d'erreur
        """
        try:
            logger.debug(f"[RulesAgent] Analyzing rules for section {section_number}")
            logger.debug(f"[RulesAgent] Content to analyze:\n{content}")
            
            # Préparer les messages pour le LLM
            messages = [
                SystemMessage(content="Tu es un expert en analyse de règles de jeu de rôle."),
                HumanMessage(content=f"""Analyse cette section et retourne un JSON avec les règles.

Section {section_number}:
{content}

INSTRUCTIONS:
1. Analyser le texte pour trouver :
   - Jets de dés (combat/chance)
   - Numéros de sections mentionnés
   - Conditions et choix

2. Retourner UNIQUEMENT ce JSON, sans explication ni commentaire :
{{
    "needs_dice": true,
    "dice_type": "combat",
    "next_sections": [2, 3],
    "conditions": ["Réussite du jet de combat"],
    "choices": ["Faire un jet de combat"],
    "rules_summary": "Jet de combat requis pour continuer"
}}

RÈGLES:
- needs_dice = true si "jet de dés", "combat", "chance"
- dice_type = "combat" si combat/HABILETÉ, "chance" si chance/CHANCE, null sinon
- next_sections = TOUS les numéros après "section", "allez à"
- Ne pas ajouter de texte avant/après le JSON
- Ne pas mettre le JSON dans des balises ```""")
            ]
            
            logger.debug(f"[RulesAgent] Sending prompt to LLM:\n{messages[1].content}")
            
            # Obtenir la réponse du LLM
            response = await self.llm.ainvoke(messages)
            logger.debug(f"[RulesAgent] LLM response:\n{response.content}")
            
            # Extraire et valider le JSON
            try:
                # Trouver le JSON dans la réponse
                json_str = response.content
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                rules = json.loads(json_str)
                logger.debug(f"[RulesAgent] Parsed rules:\n{json.dumps(rules, indent=2)}")
                
                # Valider les champs requis
                required_fields = ["needs_dice", "dice_type", "next_sections", "conditions", "choices"]
                for field in required_fields:
                    if field not in rules:
                        logger.error(f"[RulesAgent] Missing required field: {field}")
                        return None
                
                # Convertir les numéros de section en entiers
                rules["next_sections"] = [int(x) for x in rules["next_sections"]]
                
                return rules
                
            except json.JSONDecodeError as e:
                logger.error(f"[RulesAgent] Failed to parse JSON: {str(e)}")
                logger.error(f"[RulesAgent] Raw response: {response.content}")
                return None
                
        except Exception as e:
            logger.error(f"[RulesAgent] Error in _analyze_rules: {str(e)}")
            return None

    async def _load_rules_file(self, section_number: int) -> Optional[str]:
        """
        Charge le fichier de règles de manière asynchrone.
        
        Args:
            section_number: Numéro de la section
            
        Returns:
            Optional[str]: Contenu du fichier ou None si non trouvé
        """
        try:
            # Construire le chemin du fichier de règles
            rules_file = os.path.join(self.rules_directory, f"section_{section_number}_rule.md")
            
            # Vérifier si le fichier existe
            if not os.path.exists(rules_file):
                logger.warning(f"Rules file not found: {rules_file}")
                return None
            
            # Lire le contenu du fichier
            with open(rules_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading rules file: {str(e)}")
            return None

    async def ainvoke(self, input_data: Dict, config: Optional[Dict] = None) -> AsyncGenerator[Dict, None]:
        """
        Version asynchrone de invoke.
        
        Args:
            input_data (Dict): Les données d'entrée avec l'état du jeu
            config (Optional[Dict]): Configuration optionnelle
            
        Yields:
            Dict: Résultat de l'analyse des règles
        """
        try:
            state = input_data.get("state", {})
            section_number = state.get("section_number")
            
            if not section_number:
                logger.error("[RulesAgent] No section number provided")
                yield {
                    "state": {
                        "rules": {
                            "error": "No section number provided",
                            "needs_dice": False,
                            "dice_type": None,
                            "next_sections": [],
                            "conditions": [],
                            "choices": []
                        }
                    }
                }
                return

            # Récupérer le contenu de la section
            current_section = state.get("current_section", {})
            raw_content = current_section.get("content", "")
            
            if not raw_content:
                logger.error(f"[RulesAgent] No content found for section {section_number}")
                yield {
                    "state": {
                        "rules": {
                            "error": f"No content found for section {section_number}",
                            "needs_dice": False,
                            "dice_type": None,
                            "next_sections": [],
                            "conditions": [],
                            "choices": []
                        }
                    }
                }
                return
            
            # Analyser le contenu
            rules = await self._analyze_rules(section_number, raw_content)
            
            if rules:
                # Sauvegarder dans le cache
                self._save_to_cache(section_number, rules)
                
                if self.event_bus:
                    await self.event_bus.emit(
                        Event(type="rules_generated", data={
                            "section_number": section_number,
                            "rules": rules
                        })
                    )
            else:
                logger.error(f"[RulesAgent] Analysis failed for section {section_number}")
                rules = {
                    "error": f"Failed to analyze rules for section {section_number}",
                    "choices": [],
                    "needs_dice": False,
                    "dice_type": None,
                    "source": "error",
                    "raw_content": raw_content,
                    "next_sections": [],
                    "conditions": []
                }

            state["rules"] = rules
            logger.debug(f"[RulesAgent] Final state:\n{json.dumps(state, indent=2)}")
            yield {"state": state}

        except Exception as e:
            logger.error(f"[RulesAgent] Error in RulesAgent.ainvoke: {str(e)}")
            yield {
                "state": {
                    "rules": {
                        "error": str(e),
                        "needs_dice": False,
                        "dice_type": None,
                        "next_sections": [],
                        "conditions": [],
                        "choices": []
                    }
                }
            }
