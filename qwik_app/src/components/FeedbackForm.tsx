import { component$ } from '@builder.io/qwik';
import { useStore } from '@builder.io/qwik';

interface FeedbackFormProps {
  sectionId: number;
  onSubmit$: (feedback: string) => void;
}

export const FeedbackForm = component$<FeedbackFormProps>(({ sectionId, onSubmit$ }) => {
  const state = useStore({
    feedback: '',
    submitting: false
  });

  return (
    <div class="bg-white shadow-lg rounded-lg p-6">
      <h2 class="text-2xl font-bold mb-4">📝 Feedback</h2>
      <p class="text-gray-600 mb-4">
        Votre feedback nous aide à améliorer le jeu. Merci de nous dire ce que vous pensez
        de la section {sectionId}.
      </p>

      <div class="space-y-4">
        <textarea
          value={state.feedback}
          onChange$={(e) => state.feedback = (e.target as HTMLTextAreaElement).value}
          class="w-full p-2 border rounded resize-none"
          rows={6}
          placeholder="Votre feedback..."
        />

        <div class="flex justify-end space-x-4">
          <button
            onClick$={async () => {
              state.submitting = true;
              await onSubmit$(state.feedback);
              state.submitting = false;
              state.feedback = '';
            }}
            class="bg-blue-600 text-white py-2 px-6 rounded hover:bg-blue-700 transition"
            disabled={state.submitting || !state.feedback.trim()}
          >
            {state.submitting ? 'Envoi...' : 'Envoyer'}
          </button>
        </div>
      </div>
    </div>
  );
});
