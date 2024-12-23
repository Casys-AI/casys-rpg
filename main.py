"""
Point d'entrée principal de l'application Casys RPG.
"""
from api.app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=True)
