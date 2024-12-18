"""Modèle pour la narration."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class SourceType(str, Enum):
    """Type de source pour le contenu."""
    RAW = "raw"      # Contenu chargé depuis le fichier source
    CACHED = "cache" # Contenu chargé depuis le cache
    SECTION = "section" # Contenu d'une section

class NarratorModel(BaseModel):
    """Modèle pour une section narrative."""
    
    section_number: int = Field(..., gt=0, description="Numéro de la section")
    content: str = Field(default="", description="Contenu de la section")
    source_type: SourceType = Field(default=SourceType.RAW, description="Type de source")
    error: Optional[str] = Field(default=None, description="Message d'erreur si présent")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage")

    class Config:
        """Configuration du modèle."""
        from_attributes = True
