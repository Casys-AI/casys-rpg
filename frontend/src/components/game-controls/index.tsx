import { component$, useContext } from '@builder.io/qwik';
import { GameContext } from '~/routes/store';

export default component$(() => {
  const store = useContext(GameContext);

  return (
    <div class="bg-gray-800 p-4 rounded-lg shadow-lg mb-4">
      <div class="flex flex-col gap-4">
        {/* Bouton de lancer de dés */}
        <button
          onClick$={async () => {
            try {
              const response = await fetch('http://localhost:8000/game/roll-dice?dice_type=d6', {
                method: 'POST',
              });
              const data = await response.json();
              if (data.result) {
                store.diceResult = data.result;
              }
            } catch (e) {
              console.error('Erreur lors du lancer de dés:', e);
            }
          }}
          class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800"
        >
          Lancer les dés
        </button>

        {/* Résultat du dé */}
        {store.diceResult !== null && (
          <div class="text-white">
            Résultat du dé : {store.diceResult}
          </div>
        )}

        {/* Bouton de feedback */}
        <button
          onClick$={() => {
            store.feedbackMode = true;
          }}
          class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-800"
        >
          Donner un feedback
        </button>

        {/* Bouton de réinitialisation */}
        <button
          onClick$={async () => {
            try {
              const response = await fetch('http://localhost:8000/game/reset', {
                method: 'POST',
              });
              const data = await response.json();
              if (data.state) {
                store.gameState = data.state;
                store.userResponse = '';
                store.diceResult = null;
                store.feedbackMode = false;
                store.previousSection = null;
              }
            } catch (e) {
              console.error('Erreur lors de la réinitialisation:', e);
            }
          }}
          class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-800"
        >
          Réinitialiser
        </button>
      </div>
    </div>
  );
});
