from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional
import logging
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel

class NarratorAgent(RunnableSerializable[Dict, Dict]):
    """
    Agent qui lit et présente le contenu des sections.
    """
    
    sections_directory: str = Field(default="data/sections")
    llm: BaseChatModel = Field(default_factory=lambda: ChatOpenAI(model="gpt-4o-mini"))
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    cache: Dict[int, str] = Field(default_factory=dict)
    system_prompt: str = Field(default="""Tu es un narrateur qui présente le contenu d'une section.
Retourne le texte formaté pour l'affichage.""")
    event_bus: EventBus = Field(..., description="Bus d'événements pour la communication")

    class Config:
        arbitrary_types_allowed = True

    async def ainvoke(self, input: Dict) -> Dict:
        """
        Version asynchrone de l'invocation.
        """
        try:
            section_number = input.get("section_number")
            if not section_number:
                raise ValueError("Section number required")

            # Si un contenu est fourni, le formater
            if "content" in input:
                content = input["content"]
                formatted = await self._format_content(content)
                return {
                    "content": content,
                    "formatted_content": formatted
                }

            # Vérifier le cache
            if section_number in self.cache:
                content = self.cache[section_number]
                event = Event(
                    type="content_retrieved_from_cache",
                    data={
                        "section_number": section_number,
                        "content": content
                    }
                )
                await self.event_bus.emit(event)
                return {
                    "content": content,
                    "formatted_content": content
                }

            # Récupérer le contenu
            content = await self._get_content(section_number)
            
            # Mettre en cache
            self.cache[section_number] = content
            
            # Émettre l'événement
            event = Event(
                type="content_generated",
                data={
                    "section_number": section_number,
                    "content": content
                }
            )
            await self.event_bus.emit(event)
            
            return {
                "content": content,
                "formatted_content": content
            }

        except Exception as e:
            self.logger.error(f"Error in NarratorAgent: {str(e)}")
            return {"error": str(e)}

    def invoke(self, input: Dict) -> Dict:
        """
        Version synchrone de l'invocation (pour compatibilité).
        Note: Cette méthode est dépréciée, utilisez ainvoke à la place.
        """
        import warnings
        warnings.warn(
            "NarratorAgent.invoke() is deprecated, use ainvoke() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.ainvoke(input)

    async def _get_content(self, section_number: int) -> str:
        """
        Récupère le contenu d'une section.
        """
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Section: {section_number}")
            ]
            
            response = await self.llm.agenerate([messages])
            if not response.generations:
                raise ValueError("No response generated")
                
            content = response.generations[0][0].text.strip()
            return content
            
        except Exception as e:
            self.logger.warning(f"Section file not found for section {section_number}")
            return f"# Section {section_number}\nCette section n'est pas disponible."

    async def _format_content(self, content: str) -> str:
        """
        Formate le contenu pour l'affichage.
        """
        try:
            messages = [
                SystemMessage(content="Tu es un formateur de texte. Formate le texte suivant pour l'affichage."),
                HumanMessage(content=content)
            ]
            
            response = await self.llm.agenerate([messages])
            if not response.generations:
                raise ValueError("No response generated")
                
            formatted = response.generations[0][0].text.strip()
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting content: {str(e)}")
            return content
