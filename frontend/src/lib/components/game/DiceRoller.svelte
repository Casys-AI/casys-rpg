<script lang="ts">
    import { gameService } from '$lib/services/gameService';
    import type { DiceResult } from '$lib/types/game';
    
    export let diceType: string;
    export let onRoll: (result: DiceResult) => void = () => {};
    
    function rollDice(): DiceResult {
        const dice1 = Math.floor(Math.random() * 6) + 1;
        const dice2 = Math.floor(Math.random() * 6) + 1;
        return {
            dice1,
            dice2,
            total: dice1 + dice2
        };
    }
    
    async function handleRoll() {
        const result = rollDice();
        await gameService.sendChoice({
            text: `Jet de ${diceType} : ${result.total} (${result.dice1}+${result.dice2})`,
            type: 'dice_roll',
            dice_type: diceType,
            dice_results: {
                total: result.total,
                details: `${result.dice1}+${result.dice2}`,
                type: diceType
            },
            target_section: 0,
            conditions: []
        });
        onRoll(result);
    }
</script>

<div class="flex flex-col items-center gap-4 p-4 bg-gray-800 rounded-lg shadow-lg">
    <button 
        class="px-6 py-3 text-lg font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
        on:click={handleRoll}
    >
        Lancer les dés (2d6)
    </button>
    <div class="text-sm text-gray-400">
        Type de jet : {diceType}
    </div>
</div>

<style>
    button {
        min-width: 200px;
    }
</style>
