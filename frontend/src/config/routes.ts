// Routes de l'API
export const API_ROUTES = {
    // Routes de jeu
    GAME: {
        INITIALIZE: '/api/game/initialize',
        ACTION: '/api/game/action',
        STATE: '/api/game/state',
        NAVIGATE: (section: number) => `/api/game/navigate/${section}`,
        STOP: '/api/game/stop',
        RESPONSE: '/api/game/response',
        FEEDBACK: '/api/game/feedback',
    },
    
    // Routes utilitaires
    UTILS: {
        FEEDBACK: '/api/utils/feedback',
        ROLL_DICE: (diceType: string) => `/api/utils/roll/${diceType}`,
    },
    
    // Routes de streaming
    STREAM: {
        SUBSCRIBE: '/api/stream/subscribe',
        NAVIGATE: (section: number) => `/api/stream/navigate/${section}`,
    },
    
    // Routes système
    SYSTEM: {
        HEALTH: '/api/health',
        WS_INFO: '/api/ws/info',
    },
    
    // WebSocket
    WS: {
        GAME: '/ws/game',
    }
} as const;

// Types pour les routes
export type ApiRoutes = typeof API_ROUTES;
