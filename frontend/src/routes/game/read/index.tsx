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

    if (!sessionId || !gameId) {
      throw redirect(302, '/game');
    }

    const gameState = await gameService.getGameState(sessionId, gameId);
    if (!gameState) {
      throw redirect(302, '/game');
    }

    return gameState;
  } catch (error) {
    if (error instanceof Response && error.status === 302) {
      throw error;
    }
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
      return fail(401, { message: 'Session invalide' });
    }

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
      <div class="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-900 to-gray-800">
        <div class="text-center text-white">
          <div class="mb-8">
            <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
          </div>
          <h1 class="text-3xl font-bold mb-4">Chargement de votre aventure</h1>
          <p class="text-gray-400">Préparation du prochain chapitre...</p>
        </div>
      </div>
    );
  }

  return (
    <div class="py-8">
      <div class="max-w-4xl mx-auto bg-white rounded-xl shadow-2xl">
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
    </div>
  );
});

export const head: DocumentHead = {
  title: 'CASYS RPG - En jeu',
  meta: [
    {
      name: 'description',
      content: 'Plongez dans votre aventure interactive'
    }
  ]
};
