import { component$, useContext } from '@builder.io/qwik';
import { GameContext } from '~/routes/store';

export default component$(() => {
  const store = useContext(GameContext);
  const { content, error } = store.gameState;

  return (
    <div class="bg-gray-800 p-4 rounded-lg shadow-lg mb-4">
      {error && (
        <div class="bg-red-600 text-white p-4 rounded mb-4">
          {error}
        </div>
      )}
      
      {content && (
        <div class="prose prose-invert max-w-none">
          <div dangerouslySetInnerHTML={content} />
        </div>
      )}
      
      <div class="mt-6">
        <h3 class="text-xl font-bold text-white mb-4">Que souhaitez-vous faire ?</h3>
        <div class="flex gap-4">
          <input
            type="text"
            value={store.userResponse}
            onChange$={(e) => store.userResponse = (e.target as HTMLInputElement).value}
            class="flex-1 bg-gray-700 text-white p-2 rounded border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            placeholder="Votre action..."
          />
          <button
            onClick$={async () => {
              if (!store.userResponse) return;
              
              try {
                const response = await fetch('http://localhost:8000/game/action', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    user_response: store.userResponse,
                    dice_result: store.diceResult,
                  }),
                });
                
                const data = await response.json();
                if (data.error) {
                  store.gameState.error = data.error;
                } else if (data.state) {
                  store.gameState = data.state;
                  store.userResponse = '';
                  store.diceResult = null;
                }
              } catch (e) {
                store.gameState.error = "Erreur lors de la communication avec le serveur";
              }
            }}
            class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800"
          >
            Valider
          </button>
        </div>
      </div>
    </div>
  );
});
