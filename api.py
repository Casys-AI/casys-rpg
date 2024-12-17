from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
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

# Configuration du logging
setup_logging()
logger = logging.getLogger('api')

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'API
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # Utiliser IPv4
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"

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

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL du frontend Qwik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Dépendance pour obtenir le state
async def get_current_state():
    """Dépendance FastAPI pour obtenir l'état actuel du jeu"""
    global current_game_state
    if current_game_state is None:
        # Vérifier si le contenu en cache existe pour la section 1
        cache_path = os.path.join(BASE_DIR, "data/sections/cache/1_cached.md")
        content = None
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    logger.info("Contenu formaté chargé depuis le cache")
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du cache: {str(e)}")
        
        if not content:
            content = """# Bienvenue dans Casys RPG !

Vous êtes sur le point de commencer une aventure extraordinaire. 
Dans ce jeu interactif, vos choix détermineront le cours de l'histoire.

## Votre Personnage
- **Habileté**: 10
- **Endurance**: 20
- **Chance**: 8

## Ressources
- Or: 100 pièces
- Gemmes: 5

## Inventaire
- Épée
- Bouclier

*Prêt à commencer votre quête ?*"""
        
        current_game_state = GameState(
            section_number=1,
            current_section={
                "number": 1,
                "content": content,  # Contenu déjà formaté
                "choices": []
            },
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
                },
                "history": []
            },
            needs_content=False
        )
    return current_game_state

# Initialisation asynchrone des composants
async def init_components():
    """Initialise les composants qui nécessitent une boucle asyncio"""
    global story_graph, current_game_state
    
    try:
        story_graph = StoryGraph()
        success = await story_graph.initialize()
        if not success:
            logger.error("Failed to initialize StoryGraph")
            raise RuntimeError("Failed to initialize game components")
            
        current_game_state = await get_current_state()
        logger.info("Game components initialized successfully")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise RuntimeError(f"Failed to initialize game components: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de FastAPI"""
    try:
        await init_components()
        logger.info("API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {str(e)}")
        raise RuntimeError(f"Failed to start API: {str(e)}")

# Routes
@app.get("/game/state", response_model=GameResponse)
async def get_game_state(state: GameState = Depends(get_current_state)):
    """Récupère l'état actuel du jeu"""
    try:
        logger.info("Début de la route /game/state")
        logger.debug(f"Story Graph: {story_graph}")
        
        logger.info("Appel de story_graph.get_state()")
        state = await story_graph.get_state()
        logger.info("Réponse reçue de story_graph.get_state()")
        logger.debug(f"État reçu: {state}")
        
        if isinstance(state, dict):
            logger.debug("L'état est un dictionnaire")
            if "error" in state and state["error"] is not None:
                logger.error(f"Erreur dans l'état: {state['error']}")
                raise HTTPException(status_code=500, detail=state["error"])
            logger.info("Retour de l'état")
            return GameResponse(state=state)
        
        logger.info("Conversion de l'état en dictionnaire")
        return GameResponse(state=state.dict() if hasattr(state, 'dict') else state)
    except Exception as e:
        logger.error(f"Erreur détaillée dans /game/state: {str(e)}", exc_info=True)
        logger.error(f"Type d'erreur: {type(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/action")
async def process_action(action: GameAction):
    """Traite une action du joueur"""
    global current_game_state
    try:
        logger.info(f"Traitement de l'action : {action}")
        
        # Convertir l'état complet en dictionnaire et mettre à jour avec la nouvelle action
        current_state = current_game_state.dict() if current_game_state else {}
        current_state.update({
            "user_response": action.user_response,
            "dice_result": action.dice_result
        })
        
        async for new_state in story_graph.invoke(current_state):
            if "error" in new_state:
                logger.error(f"Erreur dans le traitement : {new_state['error']}")
                return GameResponse(state={}, error=new_state["error"])
            
            if "state" in new_state:
                # Mise à jour du state global avec le nouvel état complet
                current_game_state = GameState(**new_state["state"])
                logger.debug(f"Nouvel état : {new_state['state']}")
                return GameResponse(state=new_state["state"])
                
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'action : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/reset")
async def reset_game():
    """Réinitialise le jeu"""
    try:
        logger.info("Réinitialisation du jeu")
        global current_game_state
        
        # Vérifier si le contenu en cache existe pour la section 1
        cache_path = os.path.join(BASE_DIR, "data/sections/cache/1_cached.md")
        content = None
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    logger.info("Contenu formaté chargé depuis le cache")
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du cache: {str(e)}")
        
        if not content:
            content = """# Bienvenue dans Casys RPG !

Vous êtes sur le point de commencer une aventure extraordinaire. 
Dans ce jeu interactif, vos choix détermineront le cours de l'histoire.

## Votre Personnage
- **Habileté**: 10
- **Endurance**: 20
- **Chance**: 8

## Ressources
- Or: 100 pièces
- Gemmes: 5

## Inventaire
- Épée
- Bouclier

*Prêt à commencer votre quête ?*"""

        initial_state = {
            "section_number": 1,
            "current_section": {
                "number": 1,
                "content": content,
                "choices": []
            },
            "trace": {
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
                },
                "history": []
            },
            "needs_content": False
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
