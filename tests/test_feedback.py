"""
Tests for feedback functionality
"""

import pytest
from utils.feedback_utils import save_feedback
from pathlib import Path
import os
from typing import Dict, Any, List, Optional, AsyncGenerator

@pytest.fixture
def feedback_dir(tmp_path):
    """Crée un répertoire temporaire pour les fichiers de feedback"""
    feedback_path = tmp_path / "data" / "feedback"
    feedback_path.mkdir(parents=True)
    return feedback_path

def test_save_feedback(feedback_dir):
    """Test l'enregistrement du feedback"""
    # Données de test
    feedback = "Super jeu !"
    
    # Sauvegarder le feedback
    save_feedback(feedback, str(feedback_dir))
    
    # Vérifier que le fichier existe
    feedback_file = feedback_dir / "user_feedback.txt"
    assert feedback_file.exists()
    
    # Vérifier le contenu
    with open(feedback_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == feedback

def test_feedback_validation(feedback_dir):
    """Test la validation du feedback"""
    # Test avec feedback vide
    with pytest.raises(ValueError):
        save_feedback("", str(feedback_dir))
        
    # Test avec feedback trop long
    long_feedback = "x" * 1001  # Plus de 1000 caractères
    with pytest.raises(ValueError):
        save_feedback(long_feedback, str(feedback_dir))

def test_feedback_special_characters(feedback_dir):
    """Test l'enregistrement de feedback avec caractères spéciaux"""
    # Feedback avec caractères spéciaux
    special_feedback = "Test avec émojis 🎮 et accents éèà!"
    
    # Sauvegarder le feedback
    save_feedback(special_feedback, str(feedback_dir))
    
    # Vérifier le contenu
    feedback_file = feedback_dir / "user_feedback.txt"
    with open(feedback_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == special_feedback
