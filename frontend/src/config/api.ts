// Configuration de l'API
const env = import.meta.env;
const isDev = true; // En mode développement pour l'instant

// Fonction pour tester la disponibilité du serveur
async function getAvailablePort() {
    const ports = [8000, 8001];  // Essaie d'abord 8000, puis 8001
    for (const port of ports) {
        try {
            const response = await fetch(`http://localhost:${port}/api/health`);
            if (response.ok) {
                console.log(`✅ Port ${port} disponible et répond`);
                return port;
            }
        } catch (e) {
            console.log(`❌ Port ${port} non disponible`);
        }
    }
    console.log('⚠️ Aucun port disponible, utilisation du port par défaut 8000');
    return 8000; // Port par défaut si aucun n'est disponible
}

// Configuration par défaut
export const API_CONFIG = {
    BASE_URL: isDev ? 'http://localhost:8000' : env.VITE_API_URL || '',
    WS_URL: isDev ? 'ws://localhost:8000' : env.VITE_WS_URL || '',
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json',
    },
    WS_ENDPOINT: '/ws/game'  // Endpoint WebSocket
};

// Fonction pour mettre à jour la configuration avec le bon port
export async function updateApiConfig() {
    if (isDev) {
        const port = await getAvailablePort();
        API_CONFIG.BASE_URL = `http://localhost:${port}`;
        API_CONFIG.WS_URL = `ws://localhost:${port}`;
    }
}
