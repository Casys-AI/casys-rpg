import pytest
from agents.story_agents import ProcessTextTool, SaveTraceTool
import os
from datetime import datetime

@pytest.fixture
def process_text_tool():
    return ProcessTextTool()

@pytest.fixture
def save_trace_tool():
    return SaveTraceTool()

class TestProcessTextTool:
    def test_basic_text_processing(self, process_text_tool):
        text = "1. Ceci est un texte test\n2. Avec des numéros"
        choices = ["1. Premier choix", "2. Deuxième choix"]
        result = process_text_tool._run(text=text, choices=choices)
        
        assert "processed_text" in result
        assert "processed_choices" in result
        assert "1." not in result["processed_text"]
        assert all("." not in choice for choice in result["processed_choices"])

    def test_clean_game_instructions(self, process_text_tool):
        text = "Vous arrivez dans une clairière. Rendez-vous au 42. Ajoutez 1 point d'ENDURANCE."
        choices = ["1. Rendez-vous au 15", "2. Allez au 23 et ajoutez 1 point de CHANCE"]
        result = process_text_tool._run(text=text, choices=choices)
        
        assert "Vous arrivez dans une clairière." in result["processed_text"]
        assert "Rendez-vous au" not in result["processed_text"]
        assert "point d'ENDURANCE" not in result["processed_text"]
        assert all("Rendez-vous au" not in choice for choice in result["processed_choices"])
        assert all("point de CHANCE" not in choice for choice in result["processed_choices"])

    def test_preserve_narrative_elements(self, process_text_tool):
        text = "Le chevalier vous tend une épée. Elle augmente votre force de 2 points. Vous continuez votre route."
        choices = ["1. Prendre l'épée", "2. Refuser poliment"]
        result = process_text_tool._run(text=text, choices=choices)
        
        assert "Le chevalier vous tend une épée" in result["processed_text"]
        assert "Vous continuez votre route" in result["processed_text"]
        assert result["processed_choices"] == ["Prendre l'épée", "Refuser poliment"]

    def test_empty_input(self, process_text_tool):
        text = ""
        choices = []
        result = process_text_tool._run(text=text, choices=choices)
        
        assert result["processed_text"] == ""
        assert result["processed_choices"] == ["Continuer"]

    def test_choice_section_extraction(self, process_text_tool):
        """Test l'extraction des numéros de section depuis les choix."""
        choices = [
            "1. Engager la procédure d'évasion. Rendez-vous au 42",
            "2. Rester dans la cellule. Allez au 15"
        ]
        result = process_text_tool._run(text="", choices=choices)
        
        assert "choice_sections" in result
        assert len(result["choice_sections"]) == 2
        assert result["choice_sections"]["Engager la procédure d'évasion"] == 42
        assert result["choice_sections"]["Rester dans la cellule"] == 15

    def test_user_input_matching(self, process_text_tool):
        """Test la correspondance entre l'entrée utilisateur et les choix."""
        choices = [
            "1. Engager la procédure d'évasion. Rendez-vous au 42",
            "2. Rester dans la cellule. Allez au 15"
        ]
        
        # Test correspondance exacte
        result = process_text_tool._run(
            text="",
            choices=choices,
            user_input="Engager la procédure d'évasion"
        )
        assert result.get("next_section") == 42
        
        # Test correspondance partielle
        result = process_text_tool._run(
            text="",
            choices=choices,
            user_input="évasion"
        )
        assert result.get("next_section") == 42
        
        # Test correspondance avec variation
        result = process_text_tool._run(
            text="",
            choices=choices,
            user_input="Je veux m'évader"
        )
        assert result.get("next_section") == 42
        
        # Test sans correspondance
        result = process_text_tool._run(
            text="",
            choices=choices,
            user_input="faire quelque chose d'autre"
        )
        assert "next_section" not in result

class TestSaveTraceTool:
    def test_save_trace_success(self, save_trace_tool, tmp_path):
        save_trace_tool.trace_dir = str(tmp_path)
        
        text = "Test text"
        choices = ["Choice 1", "Choice 2"]
        result = save_trace_tool._run(text, choices)
        
        assert result is True
        assert len(os.listdir(tmp_path)) == 1

    def test_save_trace_error_handling(self, save_trace_tool):
        save_trace_tool.trace_dir = "/chemin/inexistant"
        
        text = "Test text"
        choices = ["Choice 1", "Choice 2"]
        result = save_trace_tool._run(text, choices)
        
        assert result is False
