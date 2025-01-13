import { gameService } from '$lib/services/gameService';
import { gameSession } from '$lib/stores/gameStore';
import type { PageLoad } from './$types';
import { browser } from '$app/environment';
import { get } from 'svelte/store';

export const load: PageLoad = async ({ fetch }) => {
    console.log('🎮 Loading game page...');
    
    // Utiliser le fetch de SvelteKit
    gameService.setFetch(fetch);

    // Si on est côté serveur, retourner un état initial vide
    if (!browser) {
        return {
            error: null,
            gameState: null
        };
    }

    // Vérifier si on a déjà une session
    const currentSession = get(gameSession);
    const hasSession = !!currentSession.gameId;
    
    try {
        let stateResponse;
        
        if (!hasSession) {
            // Initialiser une nouvelle partie
            console.log('🎲 Initializing new game...');
            const gameResponse = await gameService.initialize();
            console.log('🎲 Game response:', gameResponse);

            if (!gameResponse.success) {
                return {
                    error: gameResponse.message,
                    gameState: null
                };
            }
            
            stateResponse = {
                success: true,
                state: gameResponse.state
            };
        } else {
            // Récupérer l'état existant
            console.log('🎲 Loading existing game state...');
            stateResponse = await gameService.getGameState();
        }
        
        console.log('📥 Initial state:', stateResponse);

        return {
            error: stateResponse.success ? null : stateResponse.message,
            gameState: stateResponse.state
        };
    } catch (error) {
        console.error('❌ Error loading game:', error);
        return {
            error: error instanceof Error ? error.message : 'Une erreur est survenue',
            gameState: null
        };
    }
};
