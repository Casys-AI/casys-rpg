import { component$, useStylesScoped$, $ } from '@builder.io/qwik';
import type { GameState } from '~/types/game';

const API_BASE_URL = 'http://127.0.0.1:8000';

interface GameControlsProps {
  gameState: GameState;
}

export const GameControls = component$<GameControlsProps>(({ gameState }) => {
  useStylesScoped$(`
    .game-controls {
      display: flex;
      gap: var(--spacing-md);
      margin-top: var(--spacing-lg);
      padding: var(--spacing-md);
      background: var(--card-background);
      border-radius: var(--border-radius);
      box-shadow: var(--shadow-sm);
    }

    .control-button {
      padding: var(--spacing-sm) var(--spacing-md);
      border: none;
      border-radius: var(--border-radius);
      font-family: var(--font-secondary);
      cursor: pointer;
      transition: all var(--transition-fast);
      flex: 1;
    }

    .save-button {
      background: var(--primary-color);
      color: white;
    }

    .save-button:hover {
      background: var(--secondary-color);
    }

    .load-button {
      background: var(--background-color);
      border: 2px solid var(--primary-color);
      color: var(--primary-color);
    }

    .load-button:hover {
      background: var(--primary-color);
      color: white;
    }

    .reset-button {
      background: var(--accent-color);
      color: white;
    }

    .reset-button:hover {
      filter: brightness(1.1);
    }

    .debug-toggle {
      background: var(--background-color);
      border: 2px solid var(--border-color);
      color: var(--text-color);
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
    }

    .debug-toggle:hover {
      border-color: var(--primary-color);
    }
  `);

  const resetGame = $(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/game/reset`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Erreur lors de la réinitialisation du jeu');
      }

      const result = await response.json();
      if (result?.state) {
        Object.assign(gameState, {
          section_number: result.state.section_number,
          current_section: result.state.current_section,
          rules: result.state.rules,
          decision: result.state.decision,
          stats: result.state.stats,
          history: result.state.history,
          error: null,
          needs_content: false,
          user_response: null,
          dice_result: null,
          trace: result.state.trace,
          debug: false,
          action_message: ''
        });
      }
    } catch (e) {
      console.error('Erreur lors de la réinitialisation:', e);
    }
  });

  const saveGame = $(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/game/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(gameState),
      });
      if (!response.ok) throw new Error('Failed to save game');
    } catch (e) {
      console.error('Error saving game:', e);
    }
  });

  const loadGame = $(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/game/load`);
      if (!response.ok) throw new Error('Failed to load game');
      const data = await response.json();
      Object.assign(gameState, data);
    } catch (e) {
      console.error('Error loading game:', e);
    }
  });

  return (
    <div class="game-controls">
      <button class="control-button reset-button" onClick$={resetGame}>
        Recommencer
      </button>
      <button class="control-button save-button" onClick$={saveGame}>
        Sauvegarder
      </button>
      <button class="control-button load-button" onClick$={loadGame}>
        Charger
      </button>
    </div>
  );
});
