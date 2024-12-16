from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List, AsyncGenerator, Any
import logging
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel
import os
import json

class NarratorAgent(BaseModel):
    """
    Agent responsable de la lecture du contenu des sections.
    """
    llm: BaseChatModel = Field(default_factory=lambda: ChatOpenAI(
        model="gpt-4o-mini",
        model_kwargs={
            "system_message": """Tu es un narrateur de livre-jeu. 
            Tu dois lire et formater le contenu des sections pour une présentation agréable."""
        }
    ))
    event_bus: EventBus = Field(default_factory=EventBus)
    content_directory: str = Field(default="data/sections")
    cache: Dict[int, str] = Field(default_factory=dict)
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def invoke(self, input_data: Dict, config: Optional[Dict] = None) -> Dict:
        """
        Lit et formate le contenu d'une section.
        
        Args:
            input_data (Dict): Les données d'entrée avec l'état du jeu
            config (Optional[Dict]): Configuration optionnelle
            
        Returns:
            Dict: Le contenu formaté de la section
        """
        try:
            state = input_data.get("state", {})
            section_number = state.get("next_section", state.get("section_number"))
            use_cache = state.get("use_cache", False)
            
            if not section_number:
                return {
                    "state": {
                        "error": "Section number required",
                        "content": "",
                        "formatted_content": "",
                        "section_number": section_number
                    }
                }
            
            # Charger le contenu
            content = self._load_section_content(section_number, use_cache)
            if content is None:
                return {
                    "state": {
                        "error": f"Section {section_number} not found",
                        "content": f"Section {section_number} not found",
                        "formatted_content": f"Section {section_number} not found",
                        "source": "not_found",
                        "section_number": section_number
                    }
                }
                
            # Formater le contenu si nécessaire
            formatted_content = content if use_cache else self._format_content(content)
            
            # Retourner le résultat
            return {
                "state": {
                    "section_number": section_number,
                    "content": content,
                    "formatted_content": formatted_content,
                    "source": "cache" if use_cache else "loaded"
                }
            }

        except Exception as e:
            self.logger.error(f"Error in invoke: {str(e)}")
            return {
                "state": {
                    "error": str(e),
                    "content": "",
                    "formatted_content": ""
                }
            }

    def _load_section_content(self, section_number: int, use_cache: bool = False) -> Optional[str]:
        """
        Charge le contenu d'une section depuis le fichier.
        
        Args:
            section_number (int): Numéro de la section à charger
            use_cache (bool): Utiliser le cache si disponible
            
        Returns:
            Optional[str]: Le contenu de la section ou None si non trouvé
        """
        try:
            # Vérifier d'abord dans le cache si demandé
            cache_path = os.path.join(self.content_directory, "cache", f"{section_number}_cached.md")
            if use_cache and os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    return f.read()

            # Si pas dans le cache ou cache non demandé, charger depuis le fichier principal
            file_path = os.path.join(self.content_directory, f"section_{section_number}.md")
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Formater et sauvegarder dans le cache
            formatted_content = self._format_content(content)
            os.makedirs(os.path.join(self.content_directory, "cache"), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            
            return content

        except Exception as e:
            self.logger.error(f"Error loading section {section_number}: {str(e)}")
            return None

    def _format_content(self, content: str) -> str:
        """
        Formate le contenu d'une section en utilisant le LLM.
        
        Args:
            content (str): Le contenu brut à formater
            
        Returns:
            str: Le contenu formaté
        """
        try:
            # Préserver le formatage markdown existant
            formatted_content = content.strip()
            
            # Utiliser le LLM pour enrichir le contenu tout en préservant le formatage
            messages = [
                SystemMessage(content="""Tu es un narrateur de livre-jeu qui enrichit le contenu tout en préservant le formatage markdown existant.
                Règles importantes :
                1. TOUJOURS conserver les marqueurs markdown (*italique*, **gras**, # titres, etc.)
                2. TOUJOURS préserver la structure exacte du texte
                3. Enrichir le contenu sans modifier le formatage existant
                4. Ne pas ajouter de formatage supplémentaire aux parties non formatées
                """),
                HumanMessage(content=f"Voici le contenu à enrichir en préservant son formatage :\n\n{formatted_content}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Vérifier que le formatage est préservé
            if "*" not in response.content and "*" in content:
                self.logger.warning("Le formatage markdown a été perdu, retour au contenu original")
                return content
                
            return response.content

        except Exception as e:
            self.logger.error(f"Error formatting content: {str(e)}")
            return content  # Retourner le contenu non formaté en cas d'erreur

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """Invoke async."""
        result = await self.invoke(input_data)
        
        # Émettre l'événement de contenu généré si le contenu est présent et qu'il n'y a pas d'erreur
        if "content" in result["state"] and result["state"]["content"] and "error" not in result["state"]:
            await self.event_bus.emit(Event(
                type="content_generated",
                data={
                    "content": result["state"]["formatted_content"],
                    "section_number": result["state"]["section_number"],
                    "source": result["state"]["source"]
                }
            ))
            
        yield result

    async def get_state(self) -> Dict:
        """Récupère l'état actuel."""
        return {
            "section_number": 1,
            "content": "",
            "needs_content": True
        }

    async def update_state(self, state: Dict) -> None:
        """Met à jour l'état."""
        pass

    async def emit_event(self, event_type: str, data: Dict) -> None:
        """Émet un événement."""
        await self.event_bus.emit(Event(type=event_type, data=data))
