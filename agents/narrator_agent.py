# coding: utf-8
from typing import Dict, Optional, Any, List, AsyncGenerator
from langchain.schema.runnable import RunnableSerializable
from pydantic import BaseModel, ConfigDict, Field, computed_field
from event_bus import EventBus, Event
from agents.models import GameState
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.schema import SystemMessage, HumanMessage
from agents.base_agent import BaseAgent
import logging
import os
import json
from datetime import datetime

class SectionContent(BaseModel):
    """Model for section content"""
    raw_content: str
    formatted_content: Optional[str] = None
    cache_path: Optional[str] = None
    last_modified: Optional[datetime] = None
    
    @computed_field
    def is_cached(self) -> bool:
        return self.cache_path is not None and os.path.exists(self.cache_path)

class NarratorState(BaseModel):
    """Model for narrator state input/output"""
    section_number: int = Field(default=1, description="Current section number")
    content: Optional[str] = None
    needs_content: bool = True
    use_cache: bool = Field(default=False, description="Whether to use cached content")
    current_section: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "number": 1,
            "content": None,
            "choices": []
        }
    )
    error: Optional[str] = None
    source: Optional[str] = None
    is_welcome_section: bool = False

class NarratorConfig(BaseModel):
    """Configuration for NarratorAgent"""
    llm: Optional[BaseChatModel] = Field(
        default_factory=lambda: ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )
    )
    system_message: str = Field(
        default="""Tu es un narrateur de livre-jeu.
        Tu dois présenter le contenu des sections de manière engageante."""
    )
    content_directory: str = Field(default="data/sections")
    cache_directory: str = Field(default="data/sections/cache")
    welcome_message: str = Field(
        default="""# Bienvenue dans Casys RPG !"""
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @computed_field
    def cache_path(self) -> str:
        return os.path.join(self.content_directory, "cache")

class NarratorAgent(BaseAgent):
    """Agent responsible for narration"""

    def __init__(self, event_bus: Optional[EventBus] = None, config: Optional[NarratorConfig] = None):
        """Initialize the agent with Pydantic configuration"""
        self.event_bus = event_bus
        self.config = config or NarratorConfig()
        self.llm = self.config.llm
        self._logger = logging.getLogger(__name__)
        
        # Create necessary directories
        os.makedirs(self.config.content_directory, exist_ok=True)
        os.makedirs(self.config.cache_directory, exist_ok=True)

    async def _load_section_content(self, section_number: int) -> Optional[SectionContent]:
        """Load section content from file with caching"""
        try:
            cache_path = os.path.join(self.config.cache_directory, f"{section_number}_cached.md")
            
            # Check cache first
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    return SectionContent(
                        raw_content=content,
                        formatted_content=content,
                        cache_path=cache_path,
                        last_modified=datetime.fromtimestamp(os.path.getmtime(cache_path))
                    )
            
            # Load from source
            content_path = os.path.join(self.config.content_directory, f"{section_number}.md")
            if not os.path.exists(content_path):
                return None
                
            with open(content_path, "r", encoding="utf-8") as f:
                content = f.read()
                return SectionContent(
                    raw_content=content,
                    cache_path=cache_path
                )
                
        except Exception as e:
            self._logger.error(f"Error loading section {section_number}: {str(e)}")
            return None

    async def _format_content(self, content: SectionContent) -> SectionContent:
        """Format section content using LLM"""
        try:
            messages = [
                SystemMessage(content=self.config.system_message),
                HumanMessage(content="""Format this game book section content using Markdown:
                - Use '**' for important elements
                - Use '#' for section titles
                - Surround section numbers with [[ ]] (e.g. [[1]], [[2]], etc.)
                - Keep the section content engaging and immersive

Here's the content to format:"""),
                HumanMessage(content=content.raw_content)
            ]
            
            response = await self.llm.ainvoke(messages)
            content.formatted_content = response.content
            
            # Save to cache if path is set
            if content.cache_path:
                try:
                    with open(content.cache_path, "w", encoding="utf-8") as f:
                        f.write(content.formatted_content)
                    content.last_modified = datetime.now()
                except Exception as e:
                    self._logger.error(f"Error saving to cache: {str(e)}")
            
            return content
            
        except Exception as e:
            self._logger.error(f"Error formatting content: {str(e)}")
            content.formatted_content = content.raw_content
            return content

    async def ainvoke(self, input_data: Dict) -> AsyncGenerator[Dict, None]:
        """Process a section asynchronously"""
        try:
            # Convert input to NarratorState
            state = NarratorState(**input_data.get("state", {}))
            
            # Handle welcome section
            if state.is_welcome_section:
                content = SectionContent(raw_content=self.config.welcome_message)
                formatted = await self._format_content(content)
                state.content = formatted.formatted_content
                state.needs_content = False
                state.source = "welcome"
                yield {"state": state.model_dump()}
                return
            
            # Load and format section content
            content = await self._load_section_content(state.section_number)
            if not content:
                state.error = f"Section {state.section_number} not found"
                state.source = "not_found"
                yield {"state": state.model_dump()}
                return
            
            # Format content if needed
            if not content.formatted_content:
                content = await self._format_content(content)
            
            # Update state
            state.content = content.formatted_content
            state.needs_content = False
            state.source = "loaded" if not content.is_cached else "cache"
            if state.current_section:
                state.current_section["content"] = content.formatted_content
            
            yield {"state": state.model_dump()}
            
        except Exception as e:
            self._logger.error(f"Error in NarratorAgent.ainvoke: {str(e)}")
            yield {
                "state": NarratorState(
                    section_number=input_data.get("state", {}).get("section_number", 1),
                    error=str(e)
                ).model_dump()
            }

    async def invoke(self, state: Dict) -> Dict:
        """Synchronous version of ainvoke"""
        async for result in self.ainvoke(state):
            return result
