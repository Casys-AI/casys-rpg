from typing import Dict, Optional, Any, List, AsyncGenerator
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, ConfigDict, Field
from event_bus import EventBus, Event
from agents.models import GameState
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import SystemMessage, HumanMessage
from agents.base_agent import BaseAgent
import logging
import os
import json

class NarratorConfig(BaseModel):
    """Configuration pour NarratorAgent."""
    llm: Optional[BaseChatModel] = Field(default_factory=lambda: ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    ))
    system_message: SystemMessage = Field(default_factory=lambda: SystemMessage(
        content="""Tu es un narrateur de livre-jeu. 
        Tu doit lire et formater le contenu des sections en md pour une présentation agréable."""
    ))
    content_directory: str = Field(default="data/sections")
    model_config = ConfigDict(arbitrary_types_allowed=True)

class NarratorAgent(BaseAgent):
    """Agent responsable de la narration."""

    def __init__(self, event_bus: EventBus, config: Optional[NarratorConfig] = None):
        """
        Initialise l'agent avec une configuration Pydantic.
        
        Args:
            event_bus: Bus d'événements
            config: Configuration Pydantic (optionnel)
        """
        super().__init__(event_bus)  # Appel au constructeur parent
        self.config = config or NarratorConfig()
        self.llm = self.config.llm
        self.system_prompt = """Tu es un narrateur de livre-jeu.
            Tu dois présenter le contenu des sections de manière engageante."""
        self.content_directory = self.config.content_directory
        self.cache = {}
        self._logger = logging.getLogger(__name__)
        
        # Créer les répertoires nécessaires
        os.makedirs(self.content_directory, exist_ok=True)
        os.makedirs(os.path.join(self.content_directory, "cache"), exist_ok=True)

    async def invoke(self, state: Dict) -> Dict:
        """
        Charge et formate le contenu d'une section.
        
        Args:
            state: État du jeu actuel
            
        Returns:
            Dict: Nouvel état avec le contenu formaté
        """
        try:
            # Extraire les valeurs clés de l'état, quel que soit le format
            section_number = state.get("section_number", state.get("sectionNumber", 1))
            needs_content = state.get("needs_content", True)
            current_content = state.get("content", state.get("current_section", {}).get("content", None))
            
            # Si c'est la section 1 et qu'il n'y a pas de contenu, utiliser le message de bienvenue
            if section_number == 1 and needs_content:
                raw_content = """# Bienvenue dans Casys RPG !

Vous êtes sur le point de commencer une aventure extraordinaire. 
Dans ce jeu interactif, vos choix détermineront le cours de l'histoire.

## Votre Personnage
- **Habileté**: 10
- **Endurance**: 20
- **Chance**: 8

## Ressources
- Or: 100 pièces
- Gemmes: 5

## Inventaire
- Épée
- Bouclier

*Prêt à commencer votre quête ?*"""
                
                # Formater le contenu de bienvenue
                formatted_content = await self._format_content(raw_content)
                
                # Retourner l'état dans le bon format
                if "current_section" in state:
                    return {
                        "state": {
                            "section_number": section_number,
                            "current_section": {
                                "number": section_number,
                                "content": formatted_content,  # Utiliser le contenu formaté directement
                                "choices": []
                            },
                            "needs_content": False
                        }
                    }
                else:
                    return {
                        "state": {
                            "sectionNumber": section_number,
                            "content": formatted_content,  # Utiliser le contenu formaté directement
                            "choices": [],
                            "needs_content": False
                        }
                    }
            
            # Pour les autres sections, vérifier d'abord le cache
            cache_path = os.path.join(self.content_directory, "cache", f"{section_number}_cached.md")
            if os.path.exists(cache_path):
                self._logger.debug(f"Utilisation du contenu en cache pour la section {section_number}")
                with open(cache_path, "r", encoding="utf-8") as f:
                    formatted_content = f.read()
                    raw_content = formatted_content  # Pour le moment, on garde le même contenu
            else:
                # Si pas dans le cache, charger et formater
                raw_content = await self._load_section_content(section_number)
                if raw_content is None:
                    error_msg = f"Section {section_number} introuvable"
                    self._logger.error(error_msg)
                    error_html = f"<p>{error_msg}</p>"
                    # Retourner l'erreur dans le bon format
                    if "current_section" in state:
                        return {
                            "state": {
                                "section_number": section_number,
                                "current_section": {
                                    "number": section_number,
                                    "content": error_msg,
                                    "choices": []
                                },
                                "formatted_content": error_html,
                                "content": error_html,
                                "needs_content": True
                            }
                        }
                    else:
                        return {
                            "state": {
                                "sectionNumber": section_number,
                                "content": error_html,
                                "raw_content": error_msg,
                                "choices": [],
                                "needs_content": True
                            }
                        }
                    
                # Formater le contenu
                formatted_content = await self._format_content(raw_content)
                
                # Sauvegarder dans le cache
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(formatted_content)
                    self._logger.debug(f"Contenu formaté sauvegardé dans le cache: {cache_path}")
                except Exception as e:
                    self._logger.error(f"Erreur lors de la sauvegarde dans le cache: {str(e)}")
            
            # Retourner l'état dans le bon format
            if "current_section" in state:
                return {
                    "state": {
                        "section_number": section_number,
                        "current_section": {
                            "number": section_number,
                            "content": formatted_content,  # Utiliser le contenu formaté directement
                            "choices": []
                        },
                        "needs_content": False
                    }
                }
            else:
                return {
                    "state": {
                        "sectionNumber": section_number,
                        "content": formatted_content,  # Utiliser le contenu formaté directement
                        "choices": [],
                        "needs_content": False
                    }
                }
            
        except Exception as e:
            error_msg = f"Erreur dans NarratorAgent.invoke: {str(e)}"
            self._logger.error(error_msg)
            error_html = f"<p>{error_msg}</p>"
            # Retourner l'erreur dans le bon format
            if "current_section" in state:
                return {
                    "state": {
                        "section_number": state.get("section_number", 1),
                        "current_section": {
                            "number": state.get("section_number", 1),
                            "content": error_msg,
                            "choices": []
                        },
                        "formatted_content": error_html,
                        "content": error_html,
                        "needs_content": True
                    }
                }
            else:
                return {
                    "state": {
                        "sectionNumber": state.get("sectionNumber", 1),
                        "content": error_html,
                        "raw_content": error_msg,
                        "choices": [],
                        "needs_content": True
                    }
                }

    async def _load_section_content(self, section_number: int, use_cache: bool = False) -> Optional[str]:
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
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_content = f.read()
                    if use_cache:
                        return cached_content

            # Si pas dans le cache ou cache non demandé, charger depuis le fichier principal
            file_path = os.path.join(self.content_directory, f"{section_number}.md")
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Retourner le contenu brut
            return content

        except Exception as e:
            self._logger.error(f"Error loading section {section_number}: {str(e)}")
            return None

    async def _format_content(self, content: str) -> str:
        """
        Formate le contenu d'une section en utilisant le LLM.
        
        Args:
            content (str): Le contenu brut à formater
            
        Returns:
            str: Le contenu formaté en HTML
        """
        try:
            # Utiliser le LLM pour enrichir le contenu et le convertir en HTML
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""Voici le contenu à enrichir et convertir en HTML tout en préservant le sens :

Contenu markdown :
{content}

Instructions :
1. Convertir les titres markdown (# et ##) en balises <h1> et <h2>
2. Convertir l'italique (*texte*) en balises <em>
3. Convertir les paragraphes en balises <p>
4. Préserver le sens et le style du texte
5. Ne donner que le contenu HTML, pas de wrapping
""")
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Vérifier que le formatage HTML est présent
            if "<h1>" not in response.content and "# " in content:
                self._logger.warning("Le formatage HTML est manquant, formatage manuel")
                # Formatage manuel basique
                formatted = content.replace("# ", "<h1>").replace("\n", "</h1>\n")
                formatted = formatted.replace("*", "<em>")
                return f"<p>{formatted}</p>"
                
            return response.content

        except Exception as e:
            self._logger.error(f"Error formatting content: {str(e)}")
            # En cas d'erreur, faire un formatage HTML basique
            return f"<p>{content}</p>"

    async def ainvoke(
            self, input_data: Dict, config: Optional[Dict] = None
        ) -> AsyncGenerator[Dict, None]:
        """
        Version asynchrone de invoke.
        
        Args:
            input_data (Dict): Les données d'entrée avec l'état du jeu
            config (Optional[Dict]): Configuration optionnelle
            
        Returns:
            AsyncGenerator[Dict, None]: Générateur asynchrone de résultats
        """
        try:
            state = input_data.get("state", input_data)
            
            # Vérifier si l'état est vide
            if isinstance(state, dict) and not state:
                yield {
                    "state": {
                        "error": "Section number required",
                        "formatted_content": "Section number required",
                        "source": "error"
                    }
                }
                return
                
            section_number = state.get("section_number", state.get("sectionNumber", 1))
            use_cache = state.get("use_cache", False)
            
            # Charger le contenu avec gestion du cache
            content = await self._load_section_content(section_number, use_cache)
            if content is None:
                error_message = f"Section {section_number} not found"
                yield {
                    "state": {
                        "error": error_message,
                        "formatted_content": error_message,
                        "source": "not_found"
                    }
                }
                return
            
            # Mettre à jour l'état avec uniquement le contenu formaté
            state["formatted_content"] = await self._format_content(content)
            state["source"] = "cache" if use_cache else "loaded"
            
            # Émettre l'événement
            event = Event(
                type="content_generated",
                data={
                    "section_number": section_number,
                    "formatted_content": state["formatted_content"],
                    "source": state["source"]
                }
            )
            await self.event_bus.emit(event)
            
            # Retourner l'état mis à jour
            yield {"state": state}
            
        except Exception as e:
            self._logger.error(f"Error in NarratorAgent.ainvoke: {str(e)}")
            yield {
                "state": {
                    "error": str(e),
                    "formatted_content": str(e),
                    "source": "error"
                }
            }

    async def _get_section_content(self, section_number: int) -> str:
        """
        Charge le contenu d'une section depuis le fichier.
        
        Args:
            section_number (int): Numéro de la section à charger
            
        Returns:
            str: Le contenu de la section
        """
        try:
            # Charger depuis le fichier principal
            file_path = os.path.join(self.content_directory, f"{section_number}.md")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Section {section_number} not found")
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return content

        except Exception as e:
            self._logger.error(f"Error loading section {section_number}: {str(e)}")
            raise

    async def get_state(self) -> Dict:
        """Récupère l'état actuel."""
        return {
            "section_number": 1,
            "formatted_content": "",
            "needs_content": True
        }

    async def update_state(self, state: Dict) -> None:
        """Met à jour l'état."""
        pass

    async def emit_event(self, event_type: str, data: Dict) -> None:
        """Émet un événement."""
        await self.event_bus.emit(Event(type=event_type, data=data))
