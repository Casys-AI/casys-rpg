import { component$ } from '@builder.io/qwik';
import { type DocumentHead, routeLoader$, Link } from '@builder.io/qwik-city';
import { gameService } from '~/services/gameService';

/**
 * Initialisation du jeu et redirection
 */
export const useGameInit = routeLoader$(async ({ redirect, cookie }) => {
  try {
    const initialState = await gameService.getGameState();
    
    // Sauvegarder les IDs dans les cookies
    cookie.set('session_id', initialState.session_id, { path: '/' });
    cookie.set('game_id', initialState.game_id, { path: '/' });
    
    // Rediriger vers le jeu
    throw redirect(302, '/game');
  } catch (error) {
    // En cas d'erreur, on redirige quand même mais sans session
    throw redirect(302, '/game');
  }
});

export default component$(() => {
  return (
    <div class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <h1 class="text-4xl font-bold mb-8">Bienvenue dans Casys RPG</h1>
        <p class="mb-8">Une aventure interactive passionnante vous attend...</p>
        <Link 
          href="/game" 
          class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Accéder au jeu
        </Link>
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: 'Casys RPG',
  meta: [
    {
      name: 'description',
      content: 'Casys RPG - Une aventure interactive'
    }
  ]
};