// Configuration de l'API
const env = import.meta.env;
const isDev = true; // En mode développement pour l'instant

// Fonction pour tester la disponibilité du serveur
async function getAvailablePort() {
    const ports = [8000, 8001];
    for (const port of ports) {
        try {
            const response = await fetch(`http://localhost:${port}/api/health`);
            if (response.ok) {
                return port;
            }
        } catch (e) {
            console.log(`Port ${port} non disponible`);
        }
    }
    return 8000; // Port par défaut si aucun n'est disponible
}

// Configuration par défaut
const defaultConfig = {
    development: {
        BASE_URL: 'http://localhost:8000',
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
export let API_CONFIG = isDev ? defaultConfig.development : defaultConfig.production;

// Fonction pour mettre à jour la configuration avec le bon port
export async function updateApiConfig() {
    const port = await getAvailablePort();
    API_CONFIG = {
        ...API_CONFIG,
        BASE_URL: `http://localhost:${port}`,
        WS_URL: `ws://localhost:${port}`
    };
    console.log(`🔌 API configurée sur le port ${port}`);
    return API_CONFIG;
}
