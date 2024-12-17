from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from agents.story_graph import StoryGraph
from agents.models import GameState
from utils.game_utils import roll_dice
import uvicorn
import logging
import os
import asyncio
from dotenv import load_dotenv
from logging_config import setup_logging

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"

# Configuration du logging
setup_logging()
logger = logging.getLogger('api')

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_DIR = os.getenv("FEEDBACK_DIR", "data/feedback")
feedback_dir = os.path.join(BASE_DIR, FEEDBACK_DIR)
os.makedirs(feedback_dir, exist_ok=True)

app = FastAPI(
    title="Casys RPG API",
    description="API pour le jeu de rôle Casys RPG",
    version="1.0.0"
)

# Modèles Pydantic pour les requêtes
class GameAction(BaseModel):
    user_response: str
    dice_result: Optional[int] = None

class GameResponse(BaseModel):
    state: Dict[str, Any]
    error: Optional[str] = None

class FeedbackRequest(BaseModel):
    feedback: str
    previous_section: Dict[str, Any]
    user_response: str
    current_section: int

# Variables globales pour le state
story_graph = None
current_game_state = None

# Initialisation asynchrone des composants
async def init_components():
    """Initialise les composants qui nécessitent une boucle asyncio"""
    global story_graph, current_game_state
    
    story_graph = StoryGraph()
    await story_graph.initialize()  # Méthode à ajouter dans StoryGraph
    
    current_game_state = GameState(
        section_number=1,
        trace={
            "stats": {
                "Caractéristiques": {
                    "Habileté": 10,
                    "Endurance": 20,
                    "Chance": 8
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

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de FastAPI"""
    await init_components()

# Routes
@app.get("/game/state")
async def get_game_state():
    """Récupère l'état actuel du jeu"""
    try:
        logger.debug("Récupération de l'état du jeu")
        return GameResponse(
            state={
                "section_number": current_game_state.section_number,
                "current_section": current_game_state.current_section,
                "character_stats": current_game_state.character_stats
            }
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'état: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/action")
async def process_action(action: GameAction):
    """Traite une action du joueur"""
    global current_game_state
    try:
        logger.debug(f"Traitement de l'action: {action}")
        current_state = {
            "section_number": current_game_state.section_number,
            "user_response": action.user_response,
            "dice_result": action.dice_result
        }
        
        async for new_state in story_graph.invoke(current_state):
            if "error" in new_state:
                logger.error(f"Erreur dans le traitement: {new_state['error']}")
                return GameResponse(state={}, error=new_state["error"])
            
            if "state" in new_state:
                # Mise à jour du state global
                current_game_state = GameState(**new_state["state"])
                logger.debug(f"Nouvel état: {new_state['state']}")
                return GameResponse(state=new_state["state"])
                
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/reset")
async def reset_game():
    """Réinitialise le jeu"""
    try:
        logger.debug("Réinitialisation du jeu")
        global current_game_state
        initial_state = {
            "section_number": 1,
            "content": None,
            "rules": None,
            "decision": None,
            "error": None,
            "needs_content": True
        }
        
        async for new_state in story_graph.invoke(initial_state):
            if "state" in new_state:
                current_game_state = GameState(**new_state["state"])
                logger.debug(f"Jeu réinitialisé avec l'état: {new_state['state']}")
                return GameResponse(state=new_state["state"])
                
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Vérifie l'état de santé de l'API"""
    return {"status": "healthy"}

@app.post("/game/feedback")
async def save_feedback(feedback_request: FeedbackRequest):
    """Sauvegarde le feedback d'un utilisateur"""
    try:
        logger.debug(f"Sauvegarde du feedback: {feedback_request}")
        feedback_file = os.path.join(
            feedback_dir,
            f"feedback_section_{feedback_request.current_section}.txt"
        )
        
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(f"Section précédente: {feedback_request.previous_section}\n")
            f.write(f"Réponse utilisateur: {feedback_request.user_response}\n")
            f.write(f"Feedback: {feedback_request.feedback}\n")
            f.write("-" * 50 + "\n")
            
        return {"status": "success", "message": "Feedback enregistré"}
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/roll-dice")
async def roll_game_dice(dice_type: str):
    """Lance les dés pour le jeu"""
    try:
        result = roll_dice(dice_type)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors du lancer de dés: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"Démarrage du serveur API sur {API_HOST}:{API_PORT}")
    uvicorn.run(
        "api:app", 
        host=API_HOST, 
        port=API_PORT, 
        reload=API_DEBUG
    )
