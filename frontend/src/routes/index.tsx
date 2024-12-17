import { component$, useContextProvider, useStore, useVisibleTask$ } from '@builder.io/qwik';
import { DocumentHead } from '@builder.io/qwik-city';
import { GameContext, GameStore, initialStore } from './store';
import CharacterStats from '~/components/character-stats';
import GameContent from '~/components/game-content';
import GameControls from '~/components/game-controls';
import FeedbackForm from '~/components/feedback-form';

export default component$(() => {
  // Initialiser le store
  const store = useStore<GameStore>(initialStore);
  useContextProvider(GameContext, store);

  // Charger l'état initial du jeu
  useVisibleTask$(async () => {
    try {
      const response = await fetch('http://localhost:8000/game/state');
      const data = await response.json();
      if (data.state) {
        store.gameState = data.state;
      }
    } catch (e) {
      console.error('Erreur lors du chargement de l\'état initial:', e);
      store.gameState.error = "Erreur lors du chargement de l'état initial";
    }
  });

  return (
    <div class="min-h-screen bg-gray-900 text-white p-8">
      <div class="max-w-6xl mx-auto">
        <header class="text-center mb-8">
          <h1 class="text-4xl font-bold mb-2">🎲 Casys RPG</h1>
          <p class="text-gray-400">Un livre dont vous êtes le héros, propulsé par l'IA</p>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Contenu principal */}
          <div class="lg:col-span-3">
            <GameContent />
          </div>

          {/* Barre latérale */}
          <div class="space-y-8">
            <CharacterStats />
            <GameControls />
          </div>
        </div>

        {/* Formulaire de feedback (modal) */}
        <FeedbackForm />
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: 'Casys RPG',
  meta: [
    {
      name: 'description',
      content: 'Un livre dont vous êtes le héros, propulsé par l\'IA',
    },
  ],
};
