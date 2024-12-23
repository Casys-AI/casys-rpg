import { component$, useSignal, useStyles$ } from '@builder.io/qwik';
import type { GameState } from '~/types/game';

interface DiceRollerProps {
  diceType: 'combat' | 'chance';
  gameState: GameState;
}

export const DiceRoller = component$<DiceRollerProps>(({ diceType, gameState }) => {
  const result = useSignal<number | null>(null);
  const rolling = useSignal(false);
  const error = useSignal<string | null>(null);

  useStyles$(`
    .dice-roller {
      padding: var(--spacing-md) var(--spacing-lg);
      margin-top: var(--spacing-lg);
      text-align: center;
    }

    .dice-type {
      font-family: var(--font-secondary);
      font-size: 1.2rem;
      color: var(--color-ink);
      margin-bottom: var(--spacing-md);
      opacity: 0.8;
    }

    .dice-button {
      position: relative;
      width: 120px;
      height: 120px;
      border-radius: 24px;
      background: var(--color-paper);
      cursor: pointer;
      transition: all 0.3s ease;
      margin: 0 auto;
      box-shadow: var(--shadow-inset);
    }

    .dice-button:not(:disabled):hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }

    .dice-button:not(:disabled):active {
      transform: translateY(1px);
      box-shadow: var(--shadow-inset);
    }

    .dice-button:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .dice-face {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-secondary);
      font-size: 2.5rem;
      color: var(--color-ink);
    }

    .rolling .dice-face {
      animation: rollDice 0.6s ease-in-out;
    }

    .result-text {
      font-family: var(--font-primary);
      font-size: 1.1rem;
      color: var(--color-ink-light);
      margin-top: var(--spacing-md);
      min-height: 1.5em;
    }

    .error-text {
      color: var(--color-error);
      font-size: 0.9rem;
      margin-top: var(--spacing-sm);
    }

    @keyframes rollDice {
      0% { transform: scale(1) rotate(0deg); }
      25% { transform: scale(0.8) rotate(90deg); }
      50% { transform: scale(1.1) rotate(180deg); }
      75% { transform: scale(0.9) rotate(270deg); }
      100% { transform: scale(1) rotate(360deg); }
    }

    @media (max-width: 768px) {
      .dice-roller {
        padding: var(--spacing-sm) var(--spacing-md);
      }

      .dice-button {
        width: 100px;
        height: 100px;
      }

      .dice-face {
        font-size: 2rem;
      }
    }
  `);

  const rollDice = $(async () => {
    if (rolling.value) return;
    
    rolling.value = true;
    result.value = null;
    error.value = null;

    try {
      const response = await fetch(`${API_CONFIG.development.BASE_URL}/game/roll-dice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dice_type: diceType })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'Erreur lors du lancer de dés');
      }
      
      const data = await response.json();
      
      // Attendre un peu pour l'animation
      await new Promise(resolve => setTimeout(resolve, 600));
      result.value = data.result;
    } catch (err) {
      console.error('Erreur:', err);
      error.value = err instanceof Error ? err.message : 'Une erreur est survenue';
    } finally {
      rolling.value = false;
    }
  });

  return (
    <div class="dice-roller">
      <h3 class="dice-type">
        {diceType === 'combat' ? 'Lancer de Combat' : 'Lancer de Chance'}
      </h3>
      
      <button 
        class={`dice-button ${rolling.value ? 'rolling' : ''}`}
        onClick$={rollDice}
        disabled={rolling.value}
      >
        <div class="dice-face">
          {result.value ?? '?'}
        </div>
      </button>

      <p class="result-text">
        {result.value && `Résultat: ${result.value}`}
        {rolling.value && 'Lancer en cours...'}
      </p>
      
      {error.value && (
        <p class="error-text">{error.value}</p>
      )}
    </div>
  );
});
