import { component$, $ } from '@builder.io/qwik';
import type { GameState } from '~/types/game';
import { API_CONFIG } from '~/config/api';

const API_BASE_URL = API_CONFIG.baseURL;

interface GameControlsProps {
  gameState: GameState;
}

export const GameControls = component$<GameControlsProps>(({ gameState }) => {
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
    <div class="flex gap-4 mt-8 p-4 bg-white rounded-lg shadow-md">
      <button 
        class="
          flex-1 px-4 py-2 rounded-md font-secondary
          bg-red-500 text-white
          hover:bg-red-600 transition-colors
          focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50
        " 
        onClick$={resetGame}
      >
        Recommencer
      </button>
      <button 
        class="
          flex-1 px-4 py-2 rounded-md font-secondary
          bg-blue-500 text-white
          hover:bg-blue-600 transition-colors
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
        " 
        onClick$={saveGame}
      >
        Sauvegarder
      </button>
      <button 
        class="
          flex-1 px-4 py-2 rounded-md font-secondary
          border-2 border-blue-500 text-blue-500
          hover:bg-blue-500 hover:text-white transition-colors
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
        " 
        onClick$={loadGame}
      >
        Charger
      </button>
    </div>
  );
});
