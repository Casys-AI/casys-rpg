<!-- Settings Menu Component -->
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let show: boolean = false;
    export let showKnowledgeGraph: boolean = false;

    function closeSettings() {
        dispatch('close');
    }

    function toggleKnowledgeGraph() {
        dispatch('toggleKnowledgeGraph');
        closeSettings();
    }

    function resetGame() {
        dispatch('reset');
    }
</script>

{#if show}
    <div class="settings-menu fixed inset-y-0 right-0 w-64 bg-game-surface shadow-neu-flat transform transition-transform duration-300 ease-in-out z-50 flex flex-col">
        <div class="p-4 border-b border-game-primary/10">
            <div class="flex items-center justify-between">
                <h2 class="text-lg font-serif font-medium text-game-primary">Paramètres</h2>
                <button
                    on:click={closeSettings}
                    class="p-2 rounded-full hover:bg-game-background/50 transition-colors duration-200"
                    aria-label="Fermer"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-game-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
        <div class="flex-1 p-4">
            <!-- Bouton Knowledge Graph -->
            <button
                on:click={toggleKnowledgeGraph}
                class="w-full text-left px-4 py-3 rounded-xl text-game-text hover:bg-game-background/50 transition-colors duration-200 flex items-center space-x-2"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {showKnowledgeGraph ? 'text-game-accent' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Knowledge Graph</span>
            </button>

            <!-- Bouton Nouvelle partie -->
            <button
                on:click={resetGame}
                class="w-full text-left px-4 py-3 rounded-xl text-game-text hover:bg-game-background/50 transition-colors duration-200 flex items-center space-x-2"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Nouvelle partie</span>
            </button>
        </div>
    </div>
{/if}
