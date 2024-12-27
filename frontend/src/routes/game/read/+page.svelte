<script lang="ts">
    import type { PageData } from './$types';
    import { onMount, onDestroy } from 'svelte';
    import { gameService } from '$lib/services/gameService';
    import type { GameState } from '$lib/types/game';
    import type { ConnectionStatus } from '$lib/services/gameService';
    import { goto } from '$app/navigation';

    export let data: PageData;

    let gameState: GameState | null = data.gameState;
    let error = data.error;
    let unsubscribe: (() => void) | null = null;
    let showSettings = false;
    let connectionStatus: ConnectionStatus;

    // S'abonner au store de statut de connexion
    gameService.connectionStatus.subscribe(status => {
        connectionStatus = status;
    });

    onMount(async () => {
        console.log(' Mounting game component...');
        
        // Initialiser le WebSocket
        const gameResponse = await gameService.initialize();
        console.log(' Game response:', gameResponse);

        if (!gameResponse.success) {
            error = gameResponse.message;
            return;
        }

        // S'abonner aux messages WebSocket
        unsubscribe = gameService.onMessage((data) => {
            console.log(' Received game update:', data);
            if (data.state) {
                gameState = data.state;
            }
        });

        // Fermer le menu quand on clique en dehors
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            if (!target.closest('.settings-menu') && !target.closest('.settings-button')) {
                showSettings = false;
            }
        };
        document.addEventListener('click', handleClickOutside);

        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    });

    onDestroy(() => {
        if (unsubscribe) {
            unsubscribe();
        }
        gameService.disconnect();
    });

    function handleChoice(choice: any) {
        gameService.sendAction('make_choice', { choice });
    }

    function toggleSettings() {
        showSettings = !showSettings;
    }

    async function resetGame() {
        // Effacer les cookies côté serveur via l'API
        const response = await fetch('/api/game/reset', {
            method: 'POST',
        });
        
        if (response.ok) {
            // Rediriger vers la page d'accueil
            await goto('/game');
        }
    }
</script>

{#if error}
    <div class="min-h-screen bg-game-background flex items-center justify-center">
        <div class="bg-game-error/5 p-6 rounded-lg shadow-lg max-w-md">
            <p class="text-game-error font-serif text-center">{error}</p>
        </div>
    </div>
{:else if gameState}
    <div class="min-h-screen bg-game-background flex flex-col">
        <!-- En-tête -->
        <header class="bg-game-background shadow-neu-flat animate-fade-in">
            <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                <div class="flex items-center justify-between">
                    <h1 class="text-3xl font-serif font-bold tracking-tight text-game-primary">
                        CASYS RPG
                    </h1>
                    <div class="flex items-center space-x-4">
                        <div class="text-game-secondary font-serif flex items-center space-x-4">
                            <span>Section: {gameState.section_number}</span>
                            {#if gameState.rules?.needs_dice}
                                <span class="px-3 py-1 rounded-lg bg-game-primary/10">
                                    Dés requis
                                </span>
                            {/if}
                        </div>
                        <!-- Bouton paramètres -->
                        <button
                            on:click={toggleSettings}
                            class="settings-button p-2 rounded-full hover:bg-game-surface/10 transition-colors"
                            aria-label="Paramètres"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path 
                                    class="{
                                        connectionStatus === 'connected' ? 'text-green-500' :
                                        connectionStatus === 'connecting' ? 'text-yellow-500' :
                                        connectionStatus === 'error' ? 'text-red-500' :
                                        'text-gray-500'
                                    }"
                                    stroke-linecap="round" 
                                    stroke-linejoin="round" 
                                    stroke-width="1.5" 
                                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path 
                                    class="text-game-primary"
                                    stroke-linecap="round" 
                                    stroke-linejoin="round" 
                                    stroke-width="1.5" 
                                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
                                />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Menu latéral -->
        {#if showSettings}
            <div class="settings-menu fixed inset-y-0 right-0 w-64 bg-game-surface/95 backdrop-blur-sm shadow-neu-flat transform transition-transform duration-300 ease-in-out z-50 flex flex-col">
                <div class="p-4 border-b border-game-primary/10">
                    <div class="flex items-center justify-between">
                        <h2 class="text-lg font-serif font-medium text-game-primary">Paramètres</h2>
                        <button
                            on:click={toggleSettings}
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

        <!-- Contenu principal -->
        <div class="flex-1 p-2 sm:p-4">
            <div class="max-w-4xl mx-auto">
                <!-- Narrative Content -->
                <div class="bg-game-surface/50 rounded-2xl p-2 sm:p-4">
                    <div class="prose prose-lg prose-game max-w-none">
                        {#if gameState.narrative}
                            <div class="font-serif text-game-text text-justify leading-relaxed whitespace-pre-wrap">
                                {@html gameState.narrative.content}
                            </div>
                        {/if}
                    </div>
                </div>

                <!-- Choices -->
                {#if gameState.rules?.choices}
                    <div class="fixed bottom-0 left-0 right-0 bg-game-surface/95 backdrop-blur-sm shadow-neu-up p-4">
                        <div class="max-w-4xl mx-auto flex flex-col sm:flex-row gap-4 justify-center">
                            {#each gameState.rules.choices as choice}
                                <button
                                    on:click={() => handleChoice(choice)}
                                    class="transform rounded-xl bg-game-background px-6 py-3 text-lg font-serif font-medium text-game-primary shadow-neu-flat hover:bg-opacity-95 active:shadow-neu-pressed transition-all duration-300 focus:outline-none"
                                >
                                    {choice.text}
                                </button>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
        </div>
    </div>
{/if}
