import { derived, get } from 'svelte/store';
import { websocketService } from '$lib/services/websocketService';
import type { GameResponse } from '$lib/types/game';
import { gameState, gameChoices } from './gameStore';

// Exposer le store de connexion
export const wsStore = websocketService.connectionStatus;

// Store dérivé pour les erreurs WebSocket
export const wsError = derived(wsStore, ($status) => 
    $status === 'error' ? 'WebSocket connection error' : null
);

// Souscrire aux messages pour mettre à jour l'état du jeu
websocketService.onMessage((data: GameResponse) => {
    if (data?.state) {
        console.log('🔄 Updating game state from WebSocket');
        gameState.setState(data.state);
        if (data.state.choices) {
            gameChoices.setAvailableChoices(data.state.choices);
        }
    }
});

// Fonction pour envoyer des messages au serveur
export function sendWSMessage(message: any) {
    websocketService.send(message);
}

// Fonction pour fermer proprement la connexion
export function closeWS() {
    websocketService.disconnect();
}

// Fonction pour réinitialiser la connexion
export function resetWS() {
    websocketService.disconnect();
    websocketService.connect();
}
