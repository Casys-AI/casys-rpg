import pytest
from app import save_feedback
from pathlib import Path
import os

@pytest.fixture
def feedback_dir(tmp_path):
    """Crée un répertoire temporaire pour les fichiers de feedback"""
    feedback_path = tmp_path / "data" / "feedback"
    feedback_path.mkdir(parents=True)
    return feedback_path

def test_save_feedback(feedback_dir, monkeypatch):
    """Test l'enregistrement du feedback"""
    # Rediriger le chemin de sauvegarde vers le répertoire de test
    monkeypatch.setattr("app.feedback_dir", str(feedback_dir))
    
    # Données de test
    feedback = "Super jeu !"
    previous_section = {"content": "# Section 1\nContenu de test"}
    user_response = "Je vais à gauche"
    current_section = 2
    
    # Sauvegarder le feedback
    filepath = save_feedback(feedback, previous_section, user_response, current_section)
    
    # Vérifier que le fichier est créé
    assert os.path.exists(filepath)
    
    # Vérifier le contenu
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# Feedback sur décision" in content
        assert "Super jeu !" in content
        assert "Section actuelle : 2" in content
        assert "Je vais à gauche" in content
        assert "# Section 1" in content

def test_feedback_validation(feedback_dir, monkeypatch):
    """Test la validation du feedback"""
    # Rediriger le chemin de sauvegarde
    monkeypatch.setattr("app.feedback_dir", str(feedback_dir))
    
    # Feedback vide
    empty_feedback = ""
    previous_section = {"content": "Test"}
    user_response = "Test"
    current_section = 1
    
    filepath = save_feedback(empty_feedback, previous_section, user_response, current_section)
    
    # Vérifier que même un feedback vide est sauvegardé
    assert os.path.exists(filepath)
    
    # Vérifier le contenu minimal
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Section actuelle : 1" in content

def test_feedback_special_characters(feedback_dir, monkeypatch):
    """Test l'enregistrement de feedback avec caractères spéciaux"""
    monkeypatch.setattr("app.feedback_dir", str(feedback_dir))
    
    # Feedback avec caractères spéciaux
    feedback = "Très bien ! 🎮 J'aime les émojis 👍"
    previous_section = {"content": "Test"}
    user_response = "Test avec émojis 🎲"
    current_section = 1
    
    filepath = save_feedback(feedback, previous_section, user_response, current_section)
    
    # Vérifier que le fichier est créé
    assert os.path.exists(filepath)
    
    # Vérifier que les caractères spéciaux sont préservés
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Très bien !" in content
        assert "🎮" in content
        assert "émojis 🎲" in content
