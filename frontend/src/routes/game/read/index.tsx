import { component$ } from '@builder.io/qwik';
import { routeLoader$, routeAction$, type DocumentHead } from '@builder.io/qwik-city';
import { GameBook } from '~/components/game/GameBook';
import { gameService } from '~/services/gameService';

/**
 * Loader pour l'état du jeu
 */
export const useGameState = routeLoader$(async ({ cookie, redirect }) => {
  try {
    const sessionId = cookie.get('session_id')?.value;
    const gameId = cookie.get('game_id')?.value;
    
    // On a besoin des deux IDs
    if (!sessionId || !gameId) {
      // Supprimer les cookies invalides
      cookie.delete('session_id');
      cookie.delete('game_id');
      throw redirect(302, '/game');
    }

    // Récupérer l'état du jeu
    try {
      const gameState = await gameService.getGameState(sessionId, gameId);
      if (!gameState) {
        // Supprimer les cookies si l'état n'existe pas
        cookie.delete('session_id');
        cookie.delete('game_id');
        throw redirect(302, '/game');
      }
      return gameState;
    } catch (error) {
      // Supprimer les cookies en cas d'erreur
      cookie.delete('session_id');
      cookie.delete('game_id');
      throw redirect(302, '/game');
    }
  } catch (error) {
    if (error instanceof Response && error.status === 302) {
      throw error;
    }
    // Supprimer les cookies en cas d'erreur inattendue
    cookie.delete('session_id');
    cookie.delete('game_id');
    throw redirect(302, '/game');
  }
});

/**
 * Action de navigation
 */
export const useNavigateAction = routeAction$(async (
  { target }: { target: string },
  { cookie, fail }
) => {
  try {
    const sessionId = cookie.get('session_id')?.value;
    const gameId = cookie.get('game_id')?.value;
    if (!sessionId || !gameId) {
      // Supprimer les cookies invalides
      cookie.delete('session_id');
      cookie.delete('game_id');
      return fail(401, { message: 'Session invalide' });
    }

    // Appeler le service de navigation
    const newState = await gameService.navigate(sessionId, gameId, target);
    return newState;
  } catch (error) {
    return fail(500, {
      message: error instanceof Error ? error.message : 'Erreur de navigation'
    });
  }
});

export default component$(() => {
  const state = useGameState();
  const navigate = useNavigateAction();

  if (!state.value) {
    return (
      <div class="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <div class="text-center">
          <h1 class="text-4xl font-bold mb-8">Chargement...</h1>
          <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div class="min-h-screen bg-white">
      <GameBook 
        gameState={state.value} 
        onNavigate$={async (target) => {
          const result = await navigate.submit({ target });
          if (result.value && !result.value.failed) {
            // Le state sera automatiquement mis à jour par le loader
          }
        }}
      />
    </div>
  );
});

export const head: DocumentHead = {
  title: 'Casys RPG - En jeu',
  meta: [
    {
      name: 'description',
      content: 'Votre aventure est en cours'
    }
  ]
};
