import { routeAction$, type RequestHandler } from '@builder.io/qwik-city';
import { isServer } from '@builder.io/qwik/build';
import { useGame } from '../hooks/useGame';
import { gameService } from '../services/gameService';

/**
 * Middleware pour la gestion de l'état du jeu
 */
export const onRequest: RequestHandler = async ({ redirect, cookie, url }) => {
  // Ne pas appliquer le middleware sur la page d'accueil
  if (url.pathname === '/') {
    return;
  }

  const sessionId = cookie.get('session_id')?.value;
  const gameId = cookie.get('game_id')?.value;

  // Si on est sur /game et qu'on a une session valide, rediriger vers /game/read
  if (url.pathname === '/game' && sessionId && gameId) {
    try {
      const state = await gameService.getGameState(sessionId, gameId);
      if (state) {
        throw redirect(302, '/game/read');
      }
    } catch (error) {
      if (error instanceof Error && error.message.includes('302')) {
        throw error;
      }
      // En cas d'erreur, supprimer les cookies
      cookie.delete('session_id', { path: '/' });
      cookie.delete('game_id', { path: '/' });
    }
    return;
  }

  // Si on est sur /game/read et qu'on n'a pas de session, rediriger vers /game
  if (url.pathname.startsWith('/game/read') && (!sessionId || !gameId)) {
    throw redirect(302, '/game');
  }
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
