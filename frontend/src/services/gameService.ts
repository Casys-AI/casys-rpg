import { API_CONFIG } from '../config/api';
import type { GameState } from '../types/game';
import { websocketService } from './websocketService';

/**
 * Assure que la connexion WebSocket est établie
 */
const ensureWebSocketConnection = async () => {
  if (!websocketService.isConnected()) {
    try {
      await websocketService.connect();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      throw error;
    }
  }
};

/**
 * Service de gestion du jeu
 */
export const gameService = {
  /**
   * Récupère l'état du jeu
   * Soit on récupère l'état existant avec sessionId et gameId
   * Soit on initialise une nouvelle partie
   */
  getGameState: async (sessionId?: string, gameId?: string): Promise<GameState | null> => {
    // S'assurer que la connexion WebSocket est établie
    await ensureWebSocketConnection();

    // Si on a les deux IDs, on récupère l'état existant
    if (sessionId && gameId) {
      console.log('Fetching game state with:', { sessionId, gameId });
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/game/state`, {
        headers: {
          ...API_CONFIG.DEFAULT_HEADERS,
          'X-Session-ID': sessionId,
          'X-Game-ID': gameId
        }
      });

      if (response.status === 404) {
        console.log('Game state not found');
        return null;
      }

      if (!response.ok) {
        const error = await response.text();
        console.error('Game state error:', error);
        throw new Error(`Erreur ${response.status}: ${error}`);
      }

      const data = await response.json();
      if (!data.state) {
        console.error('No state in response:', data);
        throw new Error('État du jeu invalide');
      }
      return data.state;
    }

    // Sinon on initialise une nouvelle partie
    console.log('Initializing new game');
    
    const initResponse = await fetch(`${API_CONFIG.BASE_URL}/api/game/initialize`, {
      method: 'POST',
      headers: API_CONFIG.DEFAULT_HEADERS
    });

    if (!initResponse.ok) {
      const error = await initResponse.text();
      console.error('Init error:', error);
      throw new Error(`Erreur ${initResponse.status}: ${error}`);
    }

    const initData = await initResponse.json();
    return {
      sessionId: initData.session_id,
      gameId: initData.game_id,
      ...initData.state
    };
  },

  /**
   * Lance les dés
   */
  rollDice: async (sessionId: string, gameId: string, diceType: string): Promise<number> => {
    // S'assurer que la connexion WebSocket est établie
    await ensureWebSocketConnection();

    const response = await fetch(`${API_CONFIG.BASE_URL}/api/game/roll/${diceType}`, {
      method: 'POST',
      headers: {
        ...API_CONFIG.DEFAULT_HEADERS,
        'X-Session-ID': sessionId,
        'X-Game-ID': gameId
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Erreur ${response.status}: ${error}`);
    }

    const data = await response.json();
    return data.result;
  },

  /**
   * Navigation vers une nouvelle section
   */
  navigate: async (sessionId: string, gameId: string, target: string): Promise<GameState> => {
    // S'assurer que la connexion WebSocket est établie
    await ensureWebSocketConnection();

    const response = await fetch(`${API_CONFIG.BASE_URL}/api/game/navigate/${target}`, {
      method: 'POST',
      headers: {
        ...API_CONFIG.DEFAULT_HEADERS,
        'X-Session-ID': sessionId,
        'X-Game-ID': gameId
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Erreur ${response.status}: ${error}`);
    }

    const data = await response.json();
    return data.state;
  }
};
