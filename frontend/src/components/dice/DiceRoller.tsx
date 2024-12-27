import { component$, useSignal, useTask$, $ } from '@builder.io/qwik';
import type { GameState } from '~/types/game';
import { useGame } from '~/hooks/useGame';

interface DiceRollerProps {
  diceType: 'combat' | 'chance';
  gameState: GameState;
}

interface DiceSignals {
  isRolling: boolean;
  result: number | null;
  error: string | null;
  animationFrame: number;
}

export const DiceRoller = component$<DiceRollerProps>(({ diceType, gameState }) => {
  const { actions } = useGame();
  
  const signals = useSignal<DiceSignals>({
    isRolling: false,
    result: null,
    error: null,
    animationFrame: 0
  });

  // Nettoyage automatique
  useTask$(({ cleanup }) => {
    cleanup(() => {
      signals.value = {
        ...signals.value,
        isRolling: false,
        result: null,
        error: null
      };
    });
  });

  // Animation du dé
  const animateDice = $(async () => {
    for (let i = 0; i < 10; i++) {
      signals.value = {
        ...signals.value,
        animationFrame: Math.floor(Math.random() * 6) + 1
      };
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  });

  // Lancer le dé
  const rollDice = $(async () => {
    if (signals.value.isRolling) return;
    
    try {
      signals.value = {
        ...signals.value,
        isRolling: true,
        error: null
      };

      // Animation
      await animateDice();

      // Résultat final
      const max = diceType === 'combat' ? 20 : 6;
      const result = Math.floor(Math.random() * max) + 1;
      
      signals.value = {
        ...signals.value,
        result
      };

      // Envoyer le résultat
      if (actions.handleNavigate) {
        await actions.handleNavigate(result.toString());
      }
    } catch (error) {
      signals.value = {
        ...signals.value,
        error: 'Erreur de lancement des dés'
      };
      console.error('Erreur de lancement des dés :', error);
    } finally {
      signals.value = {
        ...signals.value,
        isRolling: false
      };
    }
  });

  return (
    <div class="fixed bottom-4 right-4 p-4 bg-white rounded-lg shadow-lg">
      <div class="text-center">
        <h3 class="text-lg font-bold mb-2">
          {diceType === 'combat' ? 'Dé de combat (d20)' : 'Dé de chance (d6)'}
        </h3>
        
        <div class="relative w-20 h-20 mx-auto mb-4">
          {/* Affichage du dé */}
          <div class={`
            w-full h-full rounded-lg
            flex items-center justify-center
            text-2xl font-bold
            ${signals.value.isRolling ? 'animate-bounce' : ''}
            ${signals.value.error ? 'bg-red-100' : 'bg-gray-100'}
          `}>
            {signals.value.result || signals.value.animationFrame || '?'}
          </div>
        </div>

        {/* Bouton de lancer */}
        <button
          onClick$={rollDice}
          disabled={signals.value.isRolling}
          class={`
            px-4 py-2 rounded-lg font-bold
            ${signals.value.isRolling
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'}
          `}
        >
          {signals.value.isRolling ? 'Lancer...' : 'Lancer le dé'}
        </button>

        {/* Message d'erreur */}
        {signals.value.error && (
          <p class="mt-2 text-red-500">{signals.value.error}</p>
        )}
      </div>
    </div>
  );
});
