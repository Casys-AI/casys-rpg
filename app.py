# app.py
import random
import streamlit as st
from agents.story_graph import StoryGraph
from agents.models import GameState
from utils.game_utils import roll_dice
import logging
import os
import asyncio
from dotenv import load_dotenv
from logging_config import setup_logging

# Configuration du logging
setup_logging()
logger = logging.getLogger('app')

# Configuration des chemins
feedback_dir = os.path.join(os.path.dirname(__file__), "data", "feedback")
os.makedirs(feedback_dir, exist_ok=True)

def init_session_state():
    """Initialise l'état de la session Streamlit."""
    logger.debug("Initialisation de l'état de session")
    if "game_state" not in st.session_state:
        logger.debug("Création d'un nouveau GameState")
        game_state = GameState(
            section_number=1,  # Section de départ
            trace={
                "stats": {
                    "Caractéristiques": {
                        "Habileté": 10,
                        "Chance": 5,
                        "Endurance": 8
                    },
                    "Ressources": {
                        "Or": 100,
                        "Gemme": 5
                    },
                    "Inventaire": {
                        "Objets": ["Épée", "Bouclier"]
                    }
                }
            }
        )
        st.session_state.game_state = game_state
        
    if "story_graph" not in st.session_state:
        logger.debug("Création d'un nouveau StoryGraph")
        story_graph = StoryGraph()
        st.session_state.story_graph = story_graph
    
    if "user_response" not in st.session_state:
        st.session_state.user_response = ""
    if "feedback_mode" not in st.session_state:
        st.session_state.feedback_mode = False
    if "dice_result" not in st.session_state:
        st.session_state.dice_result = None
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False
    if "feedback_success" not in st.session_state:
        st.session_state.feedback_success = False
    if "previous_section" not in st.session_state:
        st.session_state.previous_section = None

async def render_character_stats(current_state: dict):
    """Affiche les statistiques du personnage."""
    logger.debug(f"État reçu dans render_character_stats: {current_state}")
    
    if "trace" not in current_state:
        logger.error("'trace' manquant dans l'état")
        st.error("Erreur: statistiques manquantes (trace)")
        return
        
    if "stats" not in current_state["trace"]:
        logger.error("'stats' manquant dans trace")
        st.error("Erreur: statistiques manquantes (stats)")
        return
        
    stats = current_state["trace"]["stats"]
    logger.debug(f"Stats trouvées: {stats}")
    
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
        
    if "state" not in result or "content" not in result["state"]:
        st.error("Erreur: contenu formaté manquant")
        st.write("Contenu du résultat :", result)  # Debug
        return
    
    # Style pour le texte du jeu
    st.markdown("""
    <style>
    .stMarkdown p {
        text-align: justify;
        line-height: 1.6;
        margin-bottom: 1.2em;
    }
    .stMarkdown h1 {
        color: #1E88E5;
        font-size: 2em;
        margin-bottom: 1em;
        text-align: center;
    }
    .stMarkdown h2 {
        color: #1565C0;
        font-size: 1.5em;
        margin-top: 1.5em;
        margin-bottom: 1em;
    }
    .stMarkdown em {
        color: #0D47A1;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Afficher le contenu avec le formatage HTML
    st.markdown(result["state"]["content"], unsafe_allow_html=True)
    
    # Afficher les choix dans une section distincte
    st.markdown("### Que souhaitez-vous faire ?")

async def process_user_input():
    """Traite la saisie de l'utilisateur."""
    st.session_state.user_response = st.text_input("Votre action :", key=f"user_input_{st.session_state.game_state.section_number}")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Valider") and st.session_state.user_response:
            # Sauvegarder la section actuelle avant de passer à la suivante
            current = await st.session_state.game_state.get_current_section()
            if "content" in current:
                st.session_state.previous_section = current
            
            result = await st.session_state.game_state.process_response(st.session_state.user_response)
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
                current_section = st.session_state.game_state.section_number
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
                st.rerun()
            else:
                st.warning("Veuillez entrer un feedback")
    with col2:
        if st.button("Annuler"):
            st.session_state.feedback_mode = False
            st.rerun()
    
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
            st.rerun()
        
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

async def process_game_state(game_state):
    """
    Traite l'état du jeu et retourne le premier état du générateur asynchrone.
    """
    try:
        logger.debug("Début du traitement de l'état du jeu")
        async for state in game_state:
            logger.debug(f"État reçu du générateur: {state}")
            # Vérifier et corriger l'état si nécessaire
            if not isinstance(state, dict):
                state = state.model_dump()
            
            if "trace" not in state or not state["trace"]:
                state["trace"] = {
                    "stats": {
                        "Caractéristiques": {
                            "Habileté": 10,
                            "Chance": 5,
                            "Endurance": 8
                        },
                        "Ressources": {
                            "Or": 100,
                            "Gemme": 5
                        },
                        "Inventaire": {
                            "Objets": ["Épée", "Bouclier"]
                        }
                    }
                }
            return state
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'état du jeu: {str(e)}")
        return {"error": str(e)}

async def main():
    """Point d'entrée principal de l'application."""
    try:
        logger.debug("Démarrage de l'application")
        init_session_state()
        setup_page()
        
        # Obtenir l'état actuel
        story_graph = st.session_state.story_graph
        logger.debug("StoryGraph récupéré de la session")
        
        # Traiter l'entrée utilisateur si présente
        if st.session_state.user_response:
            logger.debug(f"Traitement de la réponse utilisateur: {st.session_state.user_response}")
            current_state = {
                "section_number": st.session_state.game_state.section_number,
                "user_response": st.session_state.user_response,
                "dice_result": st.session_state.dice_result
            }
            logger.debug(f"État courant créé: {current_state}")
            result = await process_game_state(story_graph.invoke(current_state))
        else:
            logger.debug("Démarrage d'une nouvelle partie")
            # Démarrer une nouvelle partie avec la section 1
            initial_state = {
                "section_number": 1,
                "content": None,
                "rules": None,
                "decision": None,
                "error": None,
                "needs_content": True
            }
            logger.debug(f"État initial créé: {initial_state}")
            result = await process_game_state(story_graph.invoke(initial_state))
            
        logger.debug(f"Résultat final: {result}")
        
        # Afficher le contenu
        display_game_content(result)
        
        # Traiter la saisie utilisateur
        await process_user_input()
        
        # Afficher les contrôles
        render_game_controls()
        
        # Afficher les stats du personnage
        await render_character_stats(result)
        
        # Afficher le formulaire de feedback si nécessaire
        if st.session_state.feedback_mode:
            render_feedback_form()
            
    except Exception as e:
        logger.error(f"Erreur dans main: {str(e)}", exc_info=True)
        st.error(f"Une erreur s'est produite: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
