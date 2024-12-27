import { component$ } from '@builder.io/qwik';
import { type DocumentHead, routeAction$, Form, routeLoader$ } from '@builder.io/qwik-city';
import { gameService } from '~/services/gameService';

export const useGameState = routeLoader$(async ({ cookie }) => {
  const sessionId = cookie.get('session_id')?.value;
  const gameId = cookie.get('game_id')?.value;

  // Nettoyage des cookies incomplets
  if ((!sessionId && gameId) || (sessionId && !gameId)) {
    cookie.delete('session_id', { path: '/' });
    cookie.delete('game_id', { path: '/' });
    return { initialized: false };
  }

  // Vérification de l'état du jeu
  if (sessionId && gameId) {
    try {
      const gameState = await gameService.getGameState(sessionId, gameId);
      if (gameState) {
        return { initialized: true };
      }
    } catch (error) {
      console.error(' [GameState] Error:', error);
    }
    
    // En cas d'erreur ou d'état invalide, on nettoie
    cookie.delete('session_id', { path: '/' });
    cookie.delete('game_id', { path: '/' });
  }

  return { initialized: false };
});

export const useInitGame = routeAction$(async (_, { cookie }) => {
  try {
    const gameState = await gameService.getGameState();
    
    if (!gameState?.session_id || !gameState?.game_id) {
      return { success: false };
    }

    cookie.set('session_id', gameState.session_id, { path: '/' });
    cookie.set('game_id', gameState.game_id, { path: '/' });
    
    return { success: true };
  } catch (error) {
    console.error(' [InitGame] Error:', error);
    return { success: false };
  }
});

export default component$(() => {
  const gameState = useGameState();
  const action = useInitGame();

  // Si on a une session valide ou si l'initialisation a réussi
  if (gameState.value.initialized || action.value?.success) {
    return (
      <div class="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <div class="text-center">
          <h1 class="text-2xl mb-4">Session prête !</h1>
          <a 
            href="/game/read" 
            class="text-blue-400 hover:text-blue-300"
          >
            Continuer vers le jeu
          </a>
        </div>
      </div>
    );
  }

  // Sinon, afficher le formulaire d'initialisation
  return (
    <div class="min-h-screen flex items-center justify-center bg-gray-900 text-white">
      <div class="text-center">
        <h1 class="text-4xl font-bold mb-8">Initialisation du jeu</h1>
        
        {!action.value?.success && action.value && (
          <div class="mb-8 text-red-400">
            Une erreur est survenue lors de l'initialisation
          </div>
        )}

        <Form action={action}>
          <button 
            type="submit" 
            class="px-8 py-4 bg-blue-500 text-white rounded-lg font-bold
                   hover:bg-blue-600 transition-colors duration-200"
            disabled={action.isRunning}
          >
            {action.isRunning ? 'Initialisation...' : 'Commencer une partie'}
          </button>
        </Form>
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: 'Casys RPG',
  meta: [
    {
      name: 'description',
      content: 'Jeu de rôle textuel'
    }
  ]
};