import { API_CONFIG } from '../config/api';
import type { GameState } from '../types/game';

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
    // Si on a les deux IDs, on récupère l'état existant
    if (sessionId && gameId) {
      console.log('Fetching game state with:', { sessionId, gameId });
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/game/state`, {
        headers: API_CONFIG.DEFAULT_HEADERS
      });

      // Si on a un 404, ça veut dire que l'état n'existe pas
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
    if (!initData.state) {
      console.error('No state in init response:', initData);
      throw new Error('État initial invalide');
    }
    return initData.state;
  },

  /**
   * Lance les dés
   */
  rollDice: async (sessionId: string, gameId: string, diceType: string): Promise<number> => {
    const response = await fetch(`${API_CONFIG.BASE_URL}/api/game/roll`, {
      method: 'POST',
      headers: {
        ...API_CONFIG.DEFAULT_HEADERS,
        'X-Session-Id': sessionId,
        'X-Game-Id': gameId
      },
      body: JSON.stringify({ diceType })
    });

    if (!response.ok) {
      throw new Error('Erreur lors du lancer de dés');
    }

    const result = await response.json();
    return result.value;
  },

  /**
   * Navigation vers une nouvelle section
   */
  navigate: async (sessionId: string, gameId: string, target: string): Promise<GameState> => {
    const response = await fetch(`${API_CONFIG.BASE_URL}/api/game/navigate`, {
      method: 'POST',
      headers: {
        ...API_CONFIG.DEFAULT_HEADERS,
        'X-Session-Id': sessionId,
        'X-Game-Id': gameId
      },
      body: JSON.stringify({ target })
    });

    if (!response.ok) {
      throw new Error('Erreur lors de la navigation');
    }

    const data = await response.json();
    return data.state;
  }
};
