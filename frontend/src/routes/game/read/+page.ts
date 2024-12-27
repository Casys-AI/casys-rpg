import { gameService } from '$lib/services/gameService';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
    console.log('🎮 Loading game page...');
    
    // Utiliser le fetch de SvelteKit
    gameService.setFetch(fetch);
    
    // Initialiser le WebSocket et récupérer l'état initial
    const gameResponse = await gameService.initialize();
    console.log('🎲 Game response:', gameResponse);

    if (!gameResponse.success) {
        return {
            error: gameResponse.message,
            gameState: null
        };
    }

    // Récupérer l'état du jeu
    const stateResponse = await gameService.getGameState();
    console.log('📥 Initial state:', stateResponse);

    return {
        error: stateResponse.success ? null : stateResponse.message,
        gameState: stateResponse.state
    };
};
