import type { Handle } from '@sveltejs/kit';
import { gameService } from '$lib/services/gameService';

export const handle: Handle = async ({ event, resolve }) => {
  // Ne pas appliquer le middleware sur la page d'accueil
  if (event.url.pathname === '/') {
    return await resolve(event);
  }

  const sessionId = event.cookies.get('session_id');
  const gameId = event.cookies.get('game_id');

  // Si on est sur /game et qu'on a une session valide, rediriger vers /game/read
  if (event.url.pathname === '/game' && sessionId && gameId) {
    try {
      const state = await gameService.getGameState(sessionId, gameId);
      if (state) {
        return new Response(null, {
          status: 302,
          headers: { Location: '/game/read' }
        });
      }
    } catch (error) {
      // En cas d'erreur, supprimer les cookies
      event.cookies.delete('session_id', { path: '/' });
      event.cookies.delete('game_id', { path: '/' });
    }
  }

  // Si on est sur /game/read et qu'on n'a pas de session, rediriger vers /game
  if (event.url.pathname.startsWith('/game/read') && (!sessionId || !gameId)) {
    return new Response(null, {
      status: 302,
      headers: { Location: '/game' }
    });
  }

  return await resolve(event);
};
