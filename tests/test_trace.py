import pytest
import os
from streamlit_app import update_player_trace, start_new_game_trace
from datetime import datetime
import shutil

# Chemin vers le dossier de test
TEST_TRACE_DIR = "data/test_trace"
TEST_TRACE_FILE = os.path.join(TEST_TRACE_DIR, "player_decisions.md")

@pytest.fixture
def setup_test_trace():
    """Prépare l'environnement de test"""
    # Crée le dossier de test s'il n'existe pas
    os.makedirs(TEST_TRACE_DIR, exist_ok=True)
    
    # Crée un fichier de trace vide pour les tests
    with open(TEST_TRACE_FILE, 'w', encoding='utf-8') as f:
        f.write("# Journal des Décisions du Joueur\n\n")
    
    yield TEST_TRACE_FILE
    
    # Nettoyage après les tests
    shutil.rmtree(TEST_TRACE_DIR)

def test_start_new_game_trace(setup_test_trace):
    """Test la création d'une nouvelle partie"""
    start_new_game_trace()
    
    with open(TEST_TRACE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifie que les sections requises sont présentes
    assert "# Nouvelle Partie -" in content
    assert "## Statistiques du joueur" in content
    assert "- HABILETÉ :" in content
    assert "- ENDURANCE :" in content
    assert "- CHANCE :" in content
    assert "## Inventaire" in content
    assert "## Chemins empruntés" in content
    assert "- Début à la section [[1]]" in content

def test_update_player_trace(setup_test_trace):
    """Test la mise à jour du trace lors d'une décision"""
    # Simule un choix du joueur
    current_section = "1"
    next_section = "42"
    decision_text = "Vous décidez d'ouvrir la porte"
    
    update_player_trace(current_section, next_section, decision_text)
    
    with open(TEST_TRACE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifie que la décision est correctement enregistrée
    expected_path = f"- De [[{current_section}]] vers [[{next_section}]] : {decision_text}"
    assert expected_path in content

def test_multiple_decisions(setup_test_trace):
    """Test plusieurs décisions consécutives"""
    decisions = [
        ("1", "42", "Vous ouvrez la porte"),
        ("42", "108", "Vous prenez l'épée"),
        ("108", "66", "Vous combattez le monstre")
    ]
    
    for current, next_section, decision in decisions:
        update_player_trace(current, next_section, decision)
    
    with open(TEST_TRACE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifie que toutes les décisions sont présentes
    for current, next_section, decision in decisions:
        expected_path = f"- De [[{current}]] vers [[{next_section}]] : {decision}"
        assert expected_path in content

def test_new_game_preserves_history(setup_test_trace):
    """Test que la nouvelle partie préserve l'historique"""
    # Simule une première partie
    update_player_trace("1", "42", "Premier choix")
    
    # Démarre une nouvelle partie
    start_new_game_trace()
    
    with open(TEST_TRACE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifie que l'ancien choix est toujours présent
    assert "Premier choix" in content
    # Vérifie que la nouvelle partie est au début
    assert content.index("# Nouvelle Partie") < content.index("Premier choix")
