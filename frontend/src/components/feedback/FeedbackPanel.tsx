import { component$, useSignal } from '@builder.io/qwik';
import { gameFeedback } from '~/signals/gameFeedback';

interface FeedbackPanelProps {
  sectionNumber: number;
  previousSection: any;
}

export const FeedbackPanel = component$<FeedbackPanelProps>(({ sectionNumber, previousSection }) => {
  const feedback = useSignal('');
  const sending = useSignal(false);
  const success = useSignal(false);

  const submitFeedback = $(async () => {
    if (sending.value || !feedback.value.trim()) return;
    
    sending.value = true;
    success.value = false;

    try {
      const response = await fetch(`${API_CONFIG.development.BASE_URL}/game/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          feedback: feedback.value,
          previous_section: previousSection,
          current_section: sectionNumber
        }),
      });

      if (!response.ok) throw new Error('Failed to submit feedback');
      
      success.value = true;
      feedback.value = '';
    } catch (e) {
      console.error('Error submitting feedback:', e);
    } finally {
      sending.value = false;
    }
  });

  return (
    <div class="p-6 bg-white rounded-lg shadow-lg">
      <h3 class="text-blue-600 mb-4 font-secondary text-xl">
        Votre avis compte !
      </h3>
      
      <form 
        class="flex flex-col gap-4" 
        preventdefault:submit 
        onSubmit$={submitFeedback}
      >
        <textarea
          class="
            w-full min-h-[150px] p-3
            border-2 border-gray-200 rounded-lg
            font-primary resize-y
            transition-colors duration-200
            focus:outline-none focus:border-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
          "
          value={feedback.value}
          onChange$={(e) => feedback.value = (e.target as HTMLTextAreaElement).value}
          placeholder="Partagez vos impressions sur cette section..."
          disabled={sending.value}
        />
        
        <button
          type="submit"
          class="
            px-4 py-2 bg-blue-500 text-white
            rounded-lg font-secondary
            transition-colors duration-200
            hover:bg-blue-600
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
            disabled:opacity-50 disabled:cursor-not-allowed
            disabled:hover:bg-blue-500
          "
          disabled={sending.value || !feedback.value.trim()}
        >
          {sending.value ? 'Envoi...' : 'Envoyer'}
        </button>
      </form>

      {success.value && (
        <div class="
          mt-4 p-2 text-center text-green-600 
          font-secondary animate-fade-in
        ">
          Merci pour votre retour !
        </div>
      )}
    </div>
  );
});
