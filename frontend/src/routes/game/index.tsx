import { component$, useSignal, useTask$ } from '@builder.io/qwik';
import { routeLoader$, routeAction$, Form, useNavigate, type DocumentHead } from '@builder.io/qwik-city';
import { gameService } from '~/services/gameService';

/**
 * Loader pour l'état du jeu
 */
export const useGameState = routeLoader$(async ({ cookie, redirect }) => {
  const sessionId = cookie.get('session_id')?.value;
  const gameId = cookie.get('game_id')?.value;

  if (sessionId && gameId) {
    try {
      const gameState = await gameService.getGameState(sessionId, gameId);
      if (gameState) {
        throw redirect(302, '/game/read');
      }
    } catch (error) {
      if (!(error instanceof Error && error.message.includes('302'))) {
        cookie.delete('session_id', { path: '/' });
        cookie.delete('game_id', { path: '/' });
      }
    }
  }

  return { initialized: false };
});

/**
 * Action d'initialisation du jeu
 */
export const useInitGame = routeAction$(async (_, { cookie, redirect }) => {
  try {
    const gameState = await gameService.getGameState();
    if (!gameState?.sessionId || !gameState?.gameId) {
      return { success: false };
    }

    cookie.set('session_id', gameState.sessionId, { path: '/' });
    cookie.set('game_id', gameState.gameId, { path: '/' });
    
    throw redirect(302, '/game/read');
  } catch (error) {
    if (error instanceof Error && error.message.includes('302')) {
      throw error;
    }
    return { success: false };
  }
});

export default component$(() => {
  const state = useGameState();
  const initGame = useInitGame();
  const errorSignal = useSignal<string | null>(null);

  useTask$(({ track }) => {
    track(() => initGame.value?.success);
    
    if (initGame.value?.success === false) {
      errorSignal.value = 'Une erreur est survenue lors de l\'initialisation du jeu';
    } else {
      errorSignal.value = null;
    }
  });

  return (
    <div class="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div class="container mx-auto px-4 py-16">
        <div class="max-w-3xl mx-auto">
          {/* En-tête */}
          <div class="text-center mb-16">
            <h1 class="text-5xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
              CASYS RPG
            </h1>
            <p class="text-xl text-gray-300">
              Plongez dans une aventure interactive unique
            </p>
          </div>

          {/* Formulaire ou Message de Redirection */}
          <div class="bg-gray-800 rounded-lg shadow-2xl p-8 border border-gray-700">
            <Form action={initGame}>
              <div class="space-y-6">
                <div class="text-center">
                  <h2 class="text-2xl font-semibold mb-4">Commencer l'Aventure</h2>
                  <p class="text-gray-400 mb-8">
                    Êtes-vous prêt à entrer dans un monde de mystères et de défis ?
                  </p>
                </div>

                <div class="flex justify-center">
                  <button
                    type="submit"
                    class="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg
                           font-semibold text-lg shadow-lg transform transition
                           hover:scale-105 hover:shadow-xl
                           focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50"
                  >
                    Débuter l'Histoire
                  </button>
                </div>

                {errorSignal.value && (
                  <div class="mt-4 text-center text-red-400">
                    {errorSignal.value}
                  </div>
                )}
              </div>
            </Form>
          </div>

          {/* Footer */}
          <div class="mt-12 text-center text-sm text-gray-500">
            <p>
              CASYS RPG 2024 - Un jeu de rôle interactif propulsé par l'IA
            </p>
          </div>
        </div>
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: 'CASYS RPG',
  meta: [
    {
      name: 'description',
      content: 'Plongez dans une aventure interactive unique'
    }
  ]
};