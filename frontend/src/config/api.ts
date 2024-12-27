/**
 * Configuration de l'API
 * Centralise les paramètres de connexion et les utilitaires URL
 */
import { API_ROUTES } from './routes';

// Configuration de base
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:8000',
    WS_URL: 'ws://127.0.0.1:8000',
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json'
    },
    ROUTES: API_ROUTES,
    WS_ENDPOINT: API_ROUTES.WS.GAME
} as const;

/**
 * Construit une URL complète pour l'API REST
 * @param path - Chemin de l'endpoint
 * @param params - Paramètres optionnels de query
 */
export function buildUrl(path: string, params?: Record<string, string>): string {
    let url = `${API_CONFIG.BASE_URL}${path}`;
    if (params) {
        const queryParams = new URLSearchParams(params);
        url += `?${queryParams.toString()}`;
    }
    return url;
}

/**
 * Construit une URL WebSocket
 * @param path - Chemin du endpoint WebSocket (optionnel)
 */
export function buildWsUrl(path: string = API_CONFIG.WS_ENDPOINT): string {
    return `${API_CONFIG.WS_URL}${path}`;
}

export { API_CONFIG };
