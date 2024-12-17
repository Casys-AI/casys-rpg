import { component$, useContext, useSignal } from '@builder.io/qwik';
import { GameContext } from '~/routes/store';

export default component$(() => {
  const store = useContext(GameContext);
  const feedback = useSignal('');
  
  if (!store.feedbackMode) return null;
  
  return (
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div class="bg-gray-800 p-6 rounded-lg shadow-xl max-w-2xl w-full">
        <h2 class="text-2xl font-bold text-white mb-4">Donner un feedback</h2>
        
        <textarea
          value={feedback.value}
          onChange$={(e) => feedback.value = (e.target as HTMLTextAreaElement).value}
          class="w-full h-32 bg-gray-700 text-white p-2 rounded border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 mb-4"
          placeholder="Votre feedback..."
        />
        
        <div class="flex justify-end gap-4">
          <button
            onClick$={() => {
              store.feedbackMode = false;
              feedback.value = '';
            }}
            class="px-4 py-2 text-white bg-gray-600 rounded hover:bg-gray-700"
          >
            Annuler
          </button>
          
          <button
            onClick$={async () => {
              if (!feedback.value) return;
              
              try {
                const response = await fetch('http://localhost:8000/game/feedback', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    feedback: feedback.value,
                    previous_section: store.previousSection,
                    user_response: store.userResponse,
                    current_section: store.gameState.sectionNumber,
                  }),
                });
                
                if (response.ok) {
                  store.feedbackMode = false;
                  feedback.value = '';
                }
              } catch (e) {
                console.error('Erreur lors de l\'envoi du feedback:', e);
              }
            }}
            class="px-4 py-2 text-white bg-blue-600 rounded hover:bg-blue-700"
          >
            Envoyer
          </button>
        </div>
      </div>
    </div>
  );
});
