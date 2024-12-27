/**
 * Routes de l'API
 * Configuration centralisée des endpoints
 */
export const API_ROUTES = {
    GAME: {
        INITIALIZE: '/api/game/initialize',
        ACTION: '/api/game/action',
        STATE: '/api/game/state',
        NAVIGATE: (section: number) => `/api/game/navigate/${section}`,
        STOP: '/api/game/stop',
        RESPONSE: '/api/game/response'
    },
    
    SYSTEM: {
        HEALTH: '/api/health',
        WS_INFO: '/api/ws/info'
    },
    
    WS: {
        GAME: '/ws/game'
    }
} as const;

// Type pour le typage strict des routes
export type ApiRoutes = typeof API_ROUTES;
