import { component$, useStyles$, useSignal, type QRL } from '@builder.io/qwik';

interface ActionDialogProps {
  message: string;
  onSubmit$: QRL<(action: string) => void>;
}

export const ActionDialog = component$<ActionDialogProps>(({ message, onSubmit$ }) => {
  const actionInput = useSignal('');

  useStyles$(`
    .action-dialog {
      background: var(--color-paper);
      padding: var(--spacing-lg);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-soft);
      margin-top: var(--spacing-lg);
      border-left: 4px solid var(--color-primary);
    }

    .dialog-message {
      color: var(--color-ink);
      font-family: var(--font-primary);
      font-size: 1.1rem;
      line-height: 1.6;
      margin: 0 0 var(--spacing-md) 0;
    }

    .empty-dialog {
      font-style: italic;
      color: var(--color-ink-light);
    }

    .action-input-container {
      display: flex;
      gap: var(--spacing-md);
      margin-top: var(--spacing-md);
    }

    .action-input {
      flex: 1;
      padding: var(--spacing-sm) var(--spacing-md);
      border: 2px solid var(--color-ink-light);
      border-radius: var(--radius-md);
      font-family: var(--font-primary);
      font-size: 1rem;
      background: var(--color-paper);
      color: var(--color-ink);
      transition: all 0.2s ease;
    }

    .action-input:focus {
      outline: none;
      border-color: var(--color-primary);
      box-shadow: 0 0 0 2px var(--color-primary-light);
    }

    .submit-button {
      padding: var(--spacing-sm) var(--spacing-lg);
      background: var(--color-primary);
      color: white;
      border: none;
      border-radius: var(--radius-md);
      font-family: var(--font-primary);
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .submit-button:hover {
      background: var(--color-primary-dark);
      transform: translateY(-1px);
    }

    .submit-button:active {
      transform: translateY(1px);
    }

    .submit-button:disabled {
      background: var(--color-ink-light);
      cursor: not-allowed;
      transform: none;
    }
  `);

  return (
    <div class="action-dialog">
      <p class="dialog-message">
        {message || <span class="empty-dialog">En attente de votre action...</span>}
      </p>
      <form 
        class="action-input-container"
        preventdefault:submit
        onSubmit$={() => {
          if (actionInput.value.trim()) {
            onSubmit$(actionInput.value);
            actionInput.value = '';
          }
        }}
      >
        <input
          type="text"
          class="action-input"
          placeholder="Écrivez votre action ici..."
          value={actionInput.value}
          onInput$={(ev) => actionInput.value = (ev.target as HTMLInputElement).value}
        />
        <button 
          type="submit" 
          class="submit-button"
          disabled={!actionInput.value.trim()}
        >
          Valider
        </button>
      </form>
    </div>
  );
});
