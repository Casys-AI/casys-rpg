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
const defaultConfig = {
    development: {
        BASE_URL: 'http://localhost:8000', // Port par défaut
        WS_URL: 'ws://localhost:8000',
        API_VERSION: 'v1',
        HEALTH_CHECK_ENDPOINT: '/api/health',
        GAME_WS_ENDPOINT: '/ws/game'
    },
    production: {
        BASE_URL: env.VITE_API_URL || 'http://localhost:8000',
        WS_URL: env.VITE_WS_URL || 'ws://localhost:8000',
        API_VERSION: 'v1',
        HEALTH_CHECK_ENDPOINT: '/api/health',
        GAME_WS_ENDPOINT: '/ws/game'
    }
} as const;

// Configuration dynamique qui sera mise à jour avec le bon port
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  WS_URL: 'ws://localhost:8000',
  GAME_WS_ENDPOINT: '/ws/game',
  HEALTH_CHECK_ENDPOINT: '/health',
  FEEDBACK_ENDPOINT: '/feedback',
};

// Fonction pour mettre à jour la configuration avec le bon port
export async function updateApiConfig() {
  // Pour l'instant, on utilise des valeurs statiques
  return API_CONFIG;
}
