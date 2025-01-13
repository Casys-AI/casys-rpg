import type { GameResponse, GameStateResponse } from '$lib/types/game';
import { browser } from '$app/environment';
import { gameSession, gameState, gameChoices, type Choice } from '$lib/stores/gameStore';
import { websocketService } from './websocketService';
import { get } from 'svelte/store';

class GameService {
    private readonly API_BASE_URL = 'http://127.0.0.1:8000/api/game';
    private customFetch: typeof fetch = fetch;

    constructor() {
        // S'abonner aux messages WebSocket
        websocketService.onMessage(this.handleWebSocketMessage.bind(this));
    }

    private handleWebSocketMessage(data: any): void {
        try {
            // Gérer le heartbeat
            if (data.type === 'pong') {
                console.log('❤️ Heartbeat received');
                return;
            }

            // Traiter les différents types de messages
            if (data.type === 'state_update') {
                console.log('🔄 State update received:', data.state);
                if (data.state) {
                    gameState.setState(data.state);
                    if (data.state.choices) {
                        gameChoices.setAvailableChoices(data.state.choices);
                    }
                }
            } else if (data.type === 'choice_response') {
                console.log('🎲 Choice response received:', data);
                if (data.state) {
                    gameState.setState(data.state);
                    if (data.state.choices) {
                        gameChoices.setAvailableChoices(data.state.choices);
                    }
                }
            } else if (data.type === 'error') {
                console.error('❌ Error from server:', data.error);
            }
        } catch (error) {
            console.error('❌ Error handling WebSocket message:', error);
        }
    }

    setFetch(fetchFn: typeof fetch) {
        this.customFetch = fetchFn;
    }
    
    async initialize(): Promise<GameResponse> {
        console.log('🎮 Initializing game...');
        
        try {
            const response = await this.customFetch(`${this.API_BASE_URL}/initialize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });

            const data = await response.json();
            console.log('🎲 Game initialized response:', data);
            
            if (!response.ok) {
                throw new Error(data.detail?.[0]?.msg || data.message || 'Server error');
            }
            
            if (data.success) {
                if (browser) {
                    // D'abord effacer la session existante et les états
                    console.log('🔄 Resetting game session and state...');
                    await this.clearSession();
                    
                    // Stocker les nouveaux IDs
                    console.log('💾 Storing new session:', data.state.session_id, data.state.game_id);
                    gameSession.setSession(data.state.session_id, data.state.game_id);

                    // Mettre à jour l'état du jeu
                    console.log('🔄 Updating game state:', data.state);
                    gameState.setState(data.state);

                    // Mettre à jour les choix si présents
                    if (data.state.choices) {
                        console.log('🎲 Setting choices:', data.state.choices);
                        gameChoices.setAvailableChoices(data.state.choices);
                    }

                    // Connecter le WebSocket avec les nouveaux IDs
                    const wsUrl = `ws://127.0.0.1:8000/api/ws/game?session_id=${data.state.session_id}&game_id=${data.state.game_id}`;
                    websocketService.disconnect();
                    websocketService.connect();
                }
                return data;
            } 
            
            throw new Error(data.message || 'Failed to initialize game');
        } catch (error) {
            console.error('🎲 Game initialization error:', error);
            throw error;
        }
    }

    async getGameState(): Promise<GameStateResponse> {
        console.log('🎲 Getting game state...');

        // Reset les stores
        gameState.reset();
        gameChoices.reset();

        // Vérifier si on a un game_id
        const session = get(gameSession);
        if (!session.gameId) {
            console.log('❌ No game ID found in session:', session);
            return {
                success: false,
                message: 'No game ID found'
            };
        }

        try {
            const response = await this.customFetch(`${this.API_BASE_URL}/state?game_id=${session.gameId}`, {
                credentials: 'include'
            });
            const data = await response.json();
            console.log('📥 Got game state:', data);

            if (!response.ok) {
                throw new Error(data.detail?.[0]?.msg || 'Failed to get game state');
            }

            // Mettre à jour les stores
            if (data.state) {
                console.log('🎲 Updating game state:', data.state);
                gameState.setState(data.state);
                if (data.state.choices) {
                    gameChoices.setAvailableChoices(data.state.choices);
                }
            }

            return data;
        } catch (error) {
            console.error('❌ Error getting game state:', error);
            throw error;
        }
    }

    async sendAction(action: string, data: any = {}): Promise<void> {
        try {
            console.log('🎮 Sending action:', action, data);
            const message = {
                type: 'action',
                action: action,
                data: data
            };
            await websocketService.send(message);
        } catch (error) {
            console.error('❌ Error sending action:', error);
            throw error;
        }
    }

    async sendChoice(choice: Choice): Promise<void> {
        try {
            console.log('🎮 Sending choice:', choice);
            // Mettre à jour le store avec le choix sélectionné
            gameChoices.selectChoice(choice);
            
            // Récupérer l'état du jeu actuel
            const currentGameState = get(gameState);
            if (!currentGameState?.game_id) {
                throw new Error('No game ID available');
            }

            // Préparer le message au format DTO ChoiceRequest
            const message = {
                type: 'choice',
                choice: {
                    game_id: currentGameState.game_id,
                    choice_id: String(choice.target_section),
                    choice_text: choice.text,
                    metadata: {
                        type: choice.type,
                        target_section: choice.target_section,
                        conditions: choice.conditions || [],
                        dice_type: choice.dice_type || 'none',
                        dice_results: choice.dice_results || {}
                    }
                }
            };

            console.log('📤 Sending formatted choice:', message);
            await websocketService.send(message);
        } catch (error) {
            console.error('❌ Error sending choice:', error);
            throw error;
        }
    }

    disconnect(): void {
        try {
            websocketService.disconnect();
        } catch (error) {
            console.error('❌ Error disconnecting WebSocket:', error);
        }
    }

    async clearSession(): Promise<void> {
        try {
            console.log('🧹 Clearing session...');
            gameSession.clearSession();
            gameState.reset();
            gameChoices.reset();
            websocketService.disconnect();
        } catch (error) {
            console.error('❌ Error clearing session:', error);
            throw error;
        }
    }

    async reset(): Promise<void> {
        try {
            console.log('🔄 Resetting game...');
            // Fermer le WebSocket
            websocketService.disconnect();
            
            // Appeler l'API de reset
            const response = await this.customFetch(`${this.API_BASE_URL}/reset`, {
                method: 'POST',
                credentials: 'include'
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Failed to reset game');
            }

            console.log('✅ Game reset successful');
        } catch (error) {
            console.error('❌ Failed to reset game:', error);
            throw error;
        } finally {
            // Toujours effacer les cookies et l'état même si le reset échoue
            await this.clearSession();
        }
    }
}

export const gameService = new GameService();
