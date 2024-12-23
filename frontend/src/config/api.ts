// Configuration de l'API
const env = import.meta.env;
const isDev = true; // En mode développement pour l'instant

const config = {
    development: {
        BASE_URL: 'http://localhost:8001',
        WS_URL: 'ws://localhost:8001',
        API_VERSION: 'v1',
        HEALTH_CHECK_ENDPOINT: '/api/health',
        GAME_WS_ENDPOINT: '/ws/game'
    },
    production: {
        BASE_URL: env.VITE_API_URL || 'http://localhost:8001',
        WS_URL: env.VITE_WS_URL || 'ws://localhost:8001',
        API_VERSION: 'v1',
        HEALTH_CHECK_ENDPOINT: '/api/health',
        GAME_WS_ENDPOINT: '/ws/game'
    }
} as const;

// Export la configuration active
export const API_CONFIG = isDev ? config.development : config.production;
