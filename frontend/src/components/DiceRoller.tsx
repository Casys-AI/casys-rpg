import { component$, useSignal, $ } from '@builder.io/qwik';

interface DiceRollResult {
  rolls: number[];
  total: number;
  dice_type: string;
}

export const DiceRoller = component$(() => {
  const rollResult = useSignal<DiceRollResult | null>(null);
  const isRolling = useSignal(false);

  const rollDice = $(async (diceType: string) => {
    isRolling.value = true;
    try {
      const response = await fetch(`http://localhost:8000/roll/${diceType}`, {
        method: 'POST',
      });
      rollResult.value = await response.json();
    } catch (error) {
      console.error('Failed to roll dice:', error);
    } finally {
      isRolling.value = false;
    }
  });

  return (
    <div class="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
      <h3 class="text-xl font-bold mb-4">Dice Roller</h3>
      
      <div class="grid grid-cols-2 gap-2 mb-4">
        <button
          onClick$={() => rollDice('1d20')}
          class="p-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
          disabled={isRolling.value}
        >
          Roll d20
        </button>
        <button
          onClick$={() => rollDice('2d6')}
          class="p-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          disabled={isRolling.value}
        >
          Roll 2d6
        </button>
      </div>

      {isRolling.value ? (
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        </div>
      ) : rollResult.value && (
        <div class="text-center">
          <div class="text-2xl font-bold mb-2">{rollResult.value.total}</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Rolls: [{rollResult.value.rolls.join(', ')}]
          </div>
        </div>
      )}
    </div>
  );
});
