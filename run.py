"""
Script de démarrage pour l'application Casys RPG.
Lance le serveur Uvicorn avec la configuration appropriée.
"""
import uvicorn
import os
from dotenv import load_dotenv

def main():
    """
    Démarre le serveur avec la configuration par défaut.
    Pour modifier la configuration, utilisez les variables d'environnement :
    - CASYS_HOST: Hôte du serveur (défaut: 127.0.0.1)
    - CASYS_PORT: Port du serveur (défaut: 8000)
    - CASYS_RELOAD: Active le rechargement automatique (défaut: True)
    """
    # Charge les variables d'environnement
    load_dotenv()
    
    # Debug - Affiche la valeur brute
    port_value = os.getenv("CASYS_PORT", "8000")
    print(f"Valeur brute de CASYS_PORT: '{port_value}'")
    
    # Configuration du serveur
    host = os.getenv("CASYS_HOST", "127.0.0.1")
    port = int(port_value)
    reload = os.getenv("CASYS_RELOAD", "True").lower() == "true"
    
    print("=== Démarrage du serveur Casys RPG ===")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print("=====================================")
    
    # Lance le serveur
    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
