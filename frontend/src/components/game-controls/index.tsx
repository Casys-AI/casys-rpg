import { component$, useContext } from '@builder.io/qwik';
import { GameContext } from '~/routes/store';

export default component$(() => {
  const store = useContext(GameContext);

  return (
    <div class="paper-texture p-6 rounded-lg mt-6">
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
          class="book-button"
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
          class="book-button"
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
          class="book-button"
        >
          Réinitialiser
        </button>
      </div>
    </div>
  );
});
