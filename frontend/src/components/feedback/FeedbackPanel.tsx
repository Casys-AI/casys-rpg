import { component$, useStylesScoped$, useSignal, $ } from '@builder.io/qwik';

interface FeedbackPanelProps {
  sectionNumber: number;
  previousSection: any;
}

export const FeedbackPanel = component$<FeedbackPanelProps>(({ sectionNumber, previousSection }) => {
  const feedback = useSignal('');
  const sending = useSignal(false);
  const success = useSignal(false);

  useStylesScoped$(`
    .feedback-panel {
      padding: var(--spacing-lg);
      background: var(--card-background);
      border-radius: var(--border-radius);
      box-shadow: var(--shadow-md);
    }

    .feedback-title {
      color: var(--primary-color);
      margin-bottom: var(--spacing-md);
      font-family: var(--font-secondary);
    }

    .feedback-form {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
    }

    .feedback-textarea {
      width: 100%;
      min-height: 150px;
      padding: var(--spacing-sm);
      border: 2px solid var(--border-color);
      border-radius: var(--border-radius);
      font-family: var(--font-primary);
      resize: vertical;
      transition: border-color var(--transition-fast);
    }

    .feedback-textarea:focus {
      outline: none;
      border-color: var(--primary-color);
    }

    .submit-button {
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--primary-color);
      color: white;
      border: none;
      border-radius: var(--border-radius);
      font-family: var(--font-secondary);
      cursor: pointer;
      transition: all var(--transition-fast);
    }

    .submit-button:hover:not(:disabled) {
      background: var(--secondary-color);
    }

    .submit-button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .success-message {
      color: var(--health-color);
      padding: var(--spacing-sm);
      text-align: center;
      font-family: var(--font-secondary);
    }
  `);

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
    <div class="feedback-panel">
      <h3 class="feedback-title">Votre avis compte !</h3>
      
      <form class="feedback-form" preventdefault:submit onSubmit$={submitFeedback}>
        <textarea
          class="feedback-textarea"
          value={feedback.value}
          onChange$={(e) => feedback.value = (e.target as HTMLTextAreaElement).value}
          placeholder="Partagez vos impressions sur cette section..."
          disabled={sending.value}
        />
        
        <button
          type="submit"
          class="submit-button"
          disabled={sending.value || !feedback.value.trim()}
        >
          {sending.value ? 'Envoi...' : 'Envoyer'}
        </button>
      </form>

      {success.value && (
        <div class="success-message">
          Merci pour votre retour !
        </div>
      )}
    </div>
  );
});
