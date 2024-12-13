import random
import streamlit as st
from game_logic import GameState

def init_session_state():
    """Initialise l'état de la session Streamlit."""
    if "game_state" not in st.session_state:
        st.session_state.game_state = GameState()
    if "user_response" not in st.session_state:
        st.session_state.user_response = ""
    if "feedback_mode" not in st.session_state:
        st.session_state.feedback_mode = False
    if "dice_result" not in st.session_state:
        st.session_state.dice_result = None
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False
    if "show_stats" not in st.session_state:
        st.session_state.show_stats = False

def render_character_stats():
    """Affiche les statistiques du personnage."""
    stats = st.session_state.game_state.get_character_stats()
    if "error" in stats:
        st.error(stats["error"])
        return
        
    with st.sidebar:
        st.markdown("### 📊 Statistiques du personnage")
        if "Caractéristiques" in stats:
            carac = stats["Caractéristiques"]
            st.write(f"🎯 Habileté : {carac.get('Habileté', 0)}")
            st.write(f"🎲 Chance : {carac.get('Chance', 0)}")
            st.write(f"💪 Endurance : {carac.get('Endurance', 0)}")
        
        if "Ressources" in stats:
            st.markdown("### 💰 Ressources")
            for resource, value in stats["Ressources"].items():
                st.write(f"{resource} : {value}")
        
        if "Inventaire" in stats and stats["Inventaire"].get("Objets"):
            st.markdown("### 🎒 Inventaire")
            for item in stats["Inventaire"]["Objets"]:
                if item.strip():
                    st.write(f"- {item}")

def display_game_content(result):
    if not isinstance(result, dict):
        st.error("Erreur: format de données invalide")
        return
        
    if "error" in result and result["error"]:
        st.error(result["error"])
        return
        
    if "section_content" not in result:
        st.error("Erreur: contenu de section manquant")
        return
        
    content = result["section_content"]
    if not isinstance(content, str):
        st.error("Erreur: contenu de section invalide")
        return
    
    # Afficher le texte narratif avec le style personnalisé
    st.markdown(f'<div class="story-content">{content}</div>', unsafe_allow_html=True)
    
    # Afficher les choix dans une section distincte
    st.markdown("### Que souhaitez-vous faire ?")

def roll_dice() -> int:
    """
    Effectue un lancer de 2d6 (deux dés à 6 faces).
    
    Returns:
        int: valeur du lancer
    """
    # Lancer 2d6
    dice_value = random.randint(1, 6) + random.randint(1, 6)
    
    # Note : La comparaison avec le score de chance est faite par l'agent de décision
    # car elle dépend des règles qui peuvent changer
    return dice_value

def process_user_input():
    """Traite la saisie de l'utilisateur."""
    st.session_state.user_response = st.text_input("Votre action :", key=f"user_input_{st.session_state.game_state.get_current_section()}")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Valider") and st.session_state.user_response:
            result = st.session_state.game_state.process_response(st.session_state.user_response)
            if "error" in result:
                st.error(result["error"])
            else:
                # Nettoyer la saisie et remonter en haut
                st.session_state.user_response = ""
                st.rerun()
    with col2:
        if st.button("Donner un feedback"):
            st.session_state.feedback_mode = True
            st.rerun()

def render_feedback_form():
    """Affiche le formulaire de feedback."""
    st.markdown("### 📝 Feedback")
    feedback = st.text_area("Votre feedback sur la dernière décision :")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Envoyer"):
            if feedback:
                # TODO: Implémenter la sauvegarde du feedback
                st.success("Feedback envoyé !")
                st.session_state.feedback_mode = False
                st.rerun()
            else:
                st.warning("Veuillez entrer un feedback")
    with col2:
        if st.button("Annuler"):
            st.session_state.feedback_mode = False
            st.rerun()

def render_game_controls():
    """Affiche les contrôles du jeu dans la barre latérale."""
    with st.sidebar:
        st.markdown("### ⚙️ Contrôles")
        if st.button("Nouvelle partie"):
            st.session_state.game_state = GameState()
            st.session_state.user_response = ""
            st.session_state.dice_result = None
            st.rerun()
        
        st.session_state.show_stats = st.toggle(
            "Afficher les statistiques",
            value=st.session_state.show_stats
        )
        st.session_state.show_debug = st.toggle(
            "Afficher les informations de debug",
            value=st.session_state.show_debug
        )

def setup_page():
    st.set_page_config(
        page_title="Livre-Jeu",
        page_icon="📚",
        layout="centered"
    )
    
    # CSS personnalisé pour améliorer l'apparence
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .story-content {
            max-width: 800px;
            margin: 0 auto;
            text-align: justify;
            font-size: 1.1em;
            line-height: 1.6;
            font-family: "Open Sans", "Segoe UI", Roboto, -apple-system, sans-serif;
        }
        .story-content h1 {
            text-align: center;
            color: #1e3d59;
            margin-bottom: 1.5em;
            font-family: "Segoe UI", Roboto, -apple-system, sans-serif;
            font-weight: 600;
        }
        .story-content p {
            margin-bottom: 1em;
            text-indent: 2em;
        }
        .choices-section {
            max-width: 800px;
            margin: 0 auto;
            padding: 1em;
            background-color: #f5f5f5;
            border-radius: 8px;
            font-family: "Segoe UI", Roboto, -apple-system, sans-serif;
        }
        .choices-section h3 {
            margin-top: 0;
            margin-bottom: 1em;
        }
        .available-choices {
            max-width: 800px;
            margin: 1em auto;
            padding: 0.5em;
            font-family: "Segoe UI", Roboto, -apple-system, sans-serif;
            color: #666;
        }
        div.stButton > button {
            margin-top: 0.5em;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    setup_page()
    
    # Script JavaScript pour remonter en haut de la page
    st.markdown("""
        <script>
            window.scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    result = st.session_state.game_state.get_current_section()
    
    # Afficher les contrôles et stats dans la barre latérale
    render_game_controls()
    if st.session_state.show_stats:
        render_character_stats()
    
    # Afficher le contenu principal du jeu
    display_game_content(result)
    
    # Déplacer les infos de debug à la fin
    if st.session_state.get("show_debug", False):
        st.markdown("---")
        st.markdown("### Debug Info")
        st.write("Section courante:", result.get("current_section", "N/A"))
    
    # Interface utilisateur
    if st.session_state.feedback_mode:
        render_feedback_form()
    else:
        process_user_input()

if __name__ == "__main__":
    main()
