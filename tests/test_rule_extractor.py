import pytest
from pathlib import Path
from extract_rules import RuleExtractor

@pytest.fixture
def extractor():
    return RuleExtractor()

def test_extract_choices():
    extractor = RuleExtractor()
    text = "Rendez-vous au 42. Si vous préférez, allez au 156."
    choices = extractor.extract_choices(text, 1)
    assert len(choices) == 2
    assert "Choix: Section 1 → Section 42" in choices
    assert "Choix: Section 1 → Section 156" in choices

def test_extract_items():
    extractor = RuleExtractor()
    text = "Prenez l'épée. Vous pouvez utiliser la clé."
    items = extractor.extract_items(text)
    assert len(items) == 2
    assert "Objet: l'épée" in items
    assert "Objet: la clé" in items

def test_extract_stats():
    extractor = RuleExtractor()
    text = "Vous gagnez +2 points de vie. Vous perdez -1 point d'endurance."
    stats = extractor.extract_stats(text)
    assert len(stats) == 2
    assert "Stats: +2 vie" in stats
    assert "Stats: -1 endurance" in stats

def test_process_section(tmp_path):
    # Créer un fichier de section temporaire pour le test
    section_file = tmp_path / "1.md"
    section_content = """# Section 1
    Rendez-vous au 42.
    Prenez l'épée.
    Vous gagnez +2 points de vie."""
    
    section_file.write_text(section_content)
    
    extractor = RuleExtractor()
    extractor.process_section(section_file)
    
    # Vérifier que les règles ont été extraites
    assert len(extractor.rules_by_type['choix']) == 1
    assert len(extractor.rules_by_type['objets']) == 1
    assert len(extractor.rules_by_type['stats']) == 1
    
    # Vérifier les liens de section
    for rule in extractor.section_links:
        assert 1 in extractor.section_links[rule]

def test_save_rules(tmp_path):
    extractor = RuleExtractor()
    
    # Ajouter quelques règles de test
    rule = "Choix: Section 1 → Section 42"
    extractor.rules_by_type['choix'].add(rule)
    extractor.section_links[rule] = {1}
    
    # Définir le dossier de sortie temporaire
    global RULES_DIR
    RULES_DIR = tmp_path
    
    # Sauvegarder les règles
    extractor.save_rules()
    
    # Vérifier que le fichier a été créé
    assert (tmp_path / "choix.md").exists()
    content = (tmp_path / "choix.md").read_text()
    assert "[[1]]" in content
    assert rule in content
