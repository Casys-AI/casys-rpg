# app.py
import random
import streamlit as st
from game_logic import GameState
from utils.game_utils import roll_dice
import logging
import os
import asyncio

# Configuration des chemins
feedback_dir = os.path.join(os.path.dirname(__file__), "data", "feedback")
os.makedirs(feedback_dir, exist_ok=True)

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
    if "feedback_success" not in st.session_state:
        st.session_state.feedback_success = False
    if "previous_section" not in st.session_state:
        st.session_state.previous_section = None

def render_character_stats(current_state: dict):
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
    """Affiche le contenu du jeu."""
    if not result:
        st.error("Erreur: résultat vide")
        return
        
    if "error" in result and result["error"]:
        st.error(f"Erreur: {result['error']}")
        return
        
    if "content" not in result:
        st.error("Erreur: contenu de section manquant")
        st.write("Contenu du résultat :", result)  # Debug
        return
    
    # Afficher le texte narratif avec le style personnalisé
    st.markdown(f'<div class="story-content">{result["content"]}</div>', unsafe_allow_html=True)
    
    # Afficher les choix dans une section distincte
    st.markdown("### Que souhaitez-vous faire ?")

def process_user_input():
    """Traite la saisie de l'utilisateur."""
    st.session_state.user_response = st.text_input("Votre action :", key=f"user_input_{st.session_state.game_state.current_section}")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Valider") and st.session_state.user_response:
            # Sauvegarder la section actuelle avant de passer à la suivante
            current = asyncio.run(st.session_state.game_state.get_current_section())
            if "content" in current:
                st.session_state.previous_section = current
            
            result = asyncio.run(st.session_state.game_state.process_response(st.session_state.user_response))
            if "error" in result:
                st.error(result["error"])
            else:
                # Nettoyer la saisie et remonter en haut
                st.session_state.user_response = ""
                st.experimental_rerun()
    with col2:
        if st.button("Donner un feedback"):
            st.session_state.feedback_mode = True
            st.experimental_rerun()

def save_feedback(feedback: str, previous_section: dict, user_response: str, current_section: int):
    """Sauvegarde le feedback dans un fichier."""
    from datetime import datetime
    import os
    
    # Créer le nom du fichier avec timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"feedback_{timestamp}.md"
    filepath = os.path.join(feedback_dir, filename)
    
    # Formater le contenu du feedback
    content = "# Feedback sur décision\n\n"
    
    # État
    content += "## État\n"
    content += f"- Section actuelle : {current_section}\n"
    content += f"- Réponse utilisateur : {user_response}\n"
    content += f"- Décision prise : Section {current_section}\n\n"
    
    # Section précédente
    content += "## Section\n"
    if "content" in previous_section:
        content += previous_section["content"] + "\n\n"
    
    # Feedback
    content += "## Feedback\n"
    content += feedback
    
    # Sauvegarder le feedback
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath

def render_feedback_form():
    """Affiche le formulaire de feedback."""
    st.markdown("### 📝 Feedback")
    
    # Récupérer et afficher la section précédente
    if st.session_state.previous_section and "content" in st.session_state.previous_section:
        st.markdown("#### Section précédente :")
        st.markdown(f'<div class="story-content" style="opacity: 0.7">{st.session_state.previous_section["content"]}</div>', unsafe_allow_html=True)
    else:
        st.warning("Pas de section précédente disponible")
    
    feedback = st.text_area("Votre feedback sur la dernière décision :")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Envoyer"):
            if feedback:
                # Récupérer toutes les informations nécessaires
                current_section = st.session_state.game_state.current_section
                previous_section = st.session_state.previous_section
                last_response = st.session_state.user_response
                
                # Sauvegarder le feedback
                filepath = save_feedback(
                    feedback=feedback,
                    previous_section=previous_section,
                    user_response=last_response,
                    current_section=current_section
                )
                
                # Stocker le succès dans session_state pour l'afficher après le rerun
                st.session_state.feedback_success = True
                st.session_state.feedback_mode = False
                st.experimental_rerun()
            else:
                st.warning("Veuillez entrer un feedback")
    with col2:
        if st.button("Annuler"):
            st.session_state.feedback_mode = False
            st.experimental_rerun()
    
    # Afficher le message de succès s'il existe
    if "feedback_success" in st.session_state and st.session_state.feedback_success:
        st.success("Feedback envoyé !")
        del st.session_state.feedback_success  # Nettoyer pour le prochain feedback

def render_game_controls():
    """Affiche les contrôles du jeu dans la barre latérale."""
    with st.sidebar:
        st.markdown("### ⚙️ Contrôles")
        if st.button("Nouvelle partie"):
            st.session_state.game_state = GameState()
            st.session_state.user_response = ""
            st.session_state.dice_result = None
            st.experimental_rerun()
        
        st.session_state.show_stats = st.checkbox(
            "Afficher les statistiques",
            value=st.session_state.show_stats
        )
        st.session_state.show_debug = st.checkbox(
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
    
    # Obtenir l'état actuel une seule fois
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    current_state = loop.run_until_complete(st.session_state.game_state.get_current_section())
    loop.close()
    
    # Afficher les contrôles et stats dans la barre latérale
    render_game_controls()
    if st.session_state.show_stats:
        render_character_stats(current_state)
    
    # Afficher le contenu principal du jeu
    display_game_content(current_state)
    
    # Déplacer les infos de debug à la fin
    if st.session_state.get("show_debug", False):
        st.markdown("---")
        st.markdown("### Debug Info")
        st.write("Section courante:", current_state.get("section_number", "N/A"))
    
    # Interface utilisateur
    if st.session_state.feedback_mode:
        render_feedback_form()
    else:
        process_user_input()

if __name__ == "__main__":
    main()
