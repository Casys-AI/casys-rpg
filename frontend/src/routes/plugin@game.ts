import { routeAction$, type RequestHandler } from '@builder.io/qwik-city';
import { isServer } from '@builder.io/qwik/build';
import { useGame } from '../hooks/useGame';
import { gameService } from '../services/gameService';

/**
 * Middleware pour la gestion de l'état du jeu
 */
export const onRequest: RequestHandler = async () => {
  // Pour l'instant, pas de vérification de session
};

/**
 * Action pour initialiser le jeu
 */
export const useInitGame = routeAction$(async (_, { cookie }) => {
  const sessionId = cookie.get('session_id')?.value;
  const gameId = cookie.get('game_id')?.value;

  if (!sessionId || !gameId) {
    return {
      success: false,
      error: 'Session invalide'
    };
  }

  try {
    const state = await gameService.getGameState(sessionId, gameId);
    return {
      success: true,
      state
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Erreur d\'initialisation'
    };
  }
});

export { useGame, gameService };
