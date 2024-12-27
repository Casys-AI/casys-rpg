// Configuration de l'API
import { API_ROUTES } from './routes';

const env = import.meta.env;
const isDev = true; // En mode développement pour l'instant

// Configuration par défaut
const API_BASE = 'http://127.0.0.1:8000';  // IPv4 explicite
const WS_BASE = 'ws://127.0.0.1:8000';     // IPv4 explicite

export const API_CONFIG = {
    BASE_URL: API_BASE,
    WS_URL: WS_BASE,
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json',
    },
    ROUTES: API_ROUTES,
    WS_ENDPOINT: API_ROUTES.WS.GAME
};

// Fonction pour tester la disponibilité du serveur
async function getAvailablePort(): Promise<number> {
    const ports = [8001, 8000];  // Essaie d'abord 8001, puis 8000
    for (const port of ports) {
        try {
            const response = await fetch(`http://127.0.0.1:${port}${API_ROUTES.SYSTEM.HEALTH}`);
            if (response.ok) {
                console.log(`✅ Port ${port} disponible et répond`);
                return port;
            }
        } catch (e) {
            console.log(`❌ Port ${port} non disponible`);
        }
    }
    console.log('⚠️ Aucun port disponible, utilisation du port par défaut 8001');
    return 8001; // Port par défaut si aucun n'est disponible
}

// Fonction pour mettre à jour la configuration avec le bon port
export async function updateApiConfig() {
    if (isDev) {
        const port = await getAvailablePort();
        API_CONFIG.BASE_URL = `http://127.0.0.1:${port}`;
        API_CONFIG.WS_URL = `ws://127.0.0.1:${port}`;
    }
}

// Fonction utilitaire pour construire les URLs complets
export function buildUrl(path: string, params?: Record<string, string>): string {
    let url = `${API_CONFIG.BASE_URL}${path}`;
    if (params) {
        const queryString = new URLSearchParams(params).toString();
        url += `?${queryString}`;
    }
    return url;
}

// Fonction utilitaire pour construire les URLs WebSocket
export function buildWsUrl(path: string = API_CONFIG.WS_ENDPOINT): string {
    return `${API_CONFIG.WS_URL}${path}`;
}
