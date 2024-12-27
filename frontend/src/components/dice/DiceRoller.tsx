import { component$, useSignal, useStore, useTask$, $ } from '@builder.io/qwik';
import type { GameState } from '~/types/game';

interface DiceRollerProps {
  diceType: 'combat' | 'chance';
  gameState: GameState;
}

interface DiceState {
  isRolling: boolean;
  result: number | null;
  error: string | null;
}

export const DiceRoller = component$<DiceRollerProps>(({ diceType, gameState }) => {
  const diceState = useStore<DiceState>({
    isRolling: false,
    result: null,
    error: null,
  });

  const animationFrame = useSignal<number>(0);

  // Roll the dice with animation
  const rollDice = $(async () => {
    if (diceState.isRolling) return;
    
    try {
      diceState.isRolling = true;
      diceState.error = null;

      // Animate rolling
      for (let i = 0; i < 10; i++) {
        animationFrame.value = Math.floor(Math.random() * 6) + 1;
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Get final result based on dice type
      const max = diceType === 'combat' ? 20 : 6;
      const result = Math.floor(Math.random() * max) + 1;
      
      diceState.result = result;
    } catch (error) {
      diceState.error = 'Erreur de lancement des dés';
      console.error('Erreur de lancement des dés :', error);
    } finally {
      diceState.isRolling = false;
    }
  });

  // Nettoyage de l'animation
  useTask$(({ cleanup }) => {
    cleanup(() => {
      if (animationFrame.value) {
        animationFrame.value = 0;
      }
    });
  });

  return (
    <div class="flex flex-col items-center p-4">
      <div class="text-lg mb-4 text-gray-700">
        {diceType === 'combat' ? 'Lancer de combat' : 'Lancer de chance'}
      </div>

      <button
        onClick$={rollDice}
        disabled={diceState.isRolling}
        class={`
          w-32 h-32 rounded-xl
          ${diceState.isRolling ? 'bg-gray-200' : 'bg-white'}
          shadow-lg hover:shadow-xl
          transition-all duration-300
          flex items-center justify-center
          disabled:cursor-not-allowed
          disabled:opacity-50
        `}
      >
        {diceState.isRolling ? (
          <span class="text-4xl">{animationFrame.value || '?'}</span>
        ) : (
          <span class="text-4xl">{diceState.result || '?'}</span>
        )}
      </button>

      {diceState.error && (
        <div class="mt-4 text-red-500">{diceState.error}</div>
      )}

      {diceState.result && !diceState.isRolling && (
        <div class="mt-4 text-xl font-bold">
          Résultat : {diceState.result}
        </div>
      )}
    </div>
  );
});
