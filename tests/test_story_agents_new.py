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
        result = process_text_tool._run(text, choices)
        
        assert "processed_text" in result
        assert "processed_choices" in result
        assert "1." not in result["processed_text"]
        assert all("." not in choice for choice in result["processed_choices"])

    def test_single_choice_conversion(self, process_text_tool):
        text = "Un texte simple"
        choices = ["Un seul choix"]
        result = process_text_tool._run(text, choices)
        
        assert result["processed_choices"] == ["Continuer"]

    def test_empty_input_handling(self, process_text_tool):
        text = ""
        choices = []
        result = process_text_tool._run(text, choices)
        
        assert result["processed_text"] == ""
        assert isinstance(result["processed_choices"], list)

class TestSaveTraceTool:
    def test_save_trace_success(self, save_trace_tool, tmp_path):
        # Création d'un dossier temporaire pour les tests
        test_dir = tmp_path / "test_traces"
        test_dir.mkdir()
        
        section_text = "Test section"
        choices = ["Choix 1", "Choix 2"]
        
        # Configuration temporaire du chemin de sauvegarde
        save_trace_tool.trace_dir = str(test_dir)
        result = save_trace_tool._run(section_text, choices)
        
        assert result is True
        # Vérifier que le fichier a été créé
        saved_files = list(test_dir.glob("*.txt"))
        assert len(saved_files) == 1

    def test_save_trace_error_handling(self, save_trace_tool):
        # Test avec un chemin invalide
        save_trace_tool.trace_dir = "/chemin/invalide"
        result = save_trace_tool._run("Test", ["Choix"])
        
        assert result is False
