import type { GameState, GameResponse } from '$lib/types/game';
import { browser } from '$app/environment';
import { gameSession, gameState, gameChoices, type Choice } from '$lib/stores/gameStore';
import { WebSocketService } from './websocketService';

class GameService {
    private wsService: WebSocketService | null = null;
    private readonly API_BASE_URL = 'http://localhost:8000/api/game';
    private readonly WS_URL = 'ws://localhost:8000/ws';
    private customFetch: typeof fetch = fetch;
    
    setFetch(fetchFn: typeof fetch) {
        this.customFetch = fetchFn;
    }
    
    async initialize(): Promise<GameResponse> {
        console.log('🎮 Initializing game...');
        
        // D'abord effacer la session existante et les états
        gameSession.clearSession();
        gameState.reset();
        gameChoices.reset();
        
        try {
            const response = await this.customFetch(`${this.API_BASE_URL}/initialize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            console.log('🎲 Game initialized response:', data);
            
            if (!response.ok) {
                throw new Error(data.message || 'Server error');
            }
            
            if (data.success && browser) {
                // Stocker les nouveaux IDs
                gameSession.setSession(data.state.session_id, data.state.game_id);
                // Mettre à jour l'état du jeu
                gameState.setState(data.state);
                // Mettre à jour les choix si présents
                if (data.state.choices) {
                    gameChoices.setAvailableChoices(data.state.choices);
                }
                await this.connectWebSocket();
            } else {
                throw new Error(data.message || 'Failed to initialize game');
            }
            
            return data;
        } catch (error) {
            console.error('🎲 Game initialization error:', error);
            throw error;
        }
    }

    async getGameState(): Promise<GameResponse> {
        console.log('🎲 Getting game state...');
        try {
            const response = await this.customFetch(`${this.API_BASE_URL}/state`, {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                console.log('❌ No session found');
                gameState.reset();
                gameChoices.reset();
                return {
                    success: false,
                    message: 'No session found',
                    session_id: null,
                    game_id: null,
                    state: {}
                };
            }

            const data = await response.json();
            console.log('📥 Got game state:', data);
            
            // Mettre à jour le store avec le nouvel état
            if (data.success) {
                gameState.setState(data.state);
                // Mettre à jour les choix si présents
                if (data.state.choices) {
                    gameChoices.setAvailableChoices(data.state.choices);
                }
            }
            
            return {
                ...data,
                success: true
            };
        } catch (error) {
            console.error('❌ Failed to get game state:', error);
            gameState.reset();
            gameChoices.reset();
            return {
                success: false,
                message: error instanceof Error ? error.message : 'Failed to get game state',
                session_id: null,
                game_id: null,
                state: {}
            };
        }
    }

    private async connectWebSocket(): Promise<void> {
        if (this.wsService) {
            console.log('🔌 WebSocket already connected');
            return;
        }

        console.log('🔌 Connecting to WebSocket...');
        this.wsService = new WebSocketService(`${this.WS_URL}/game`);
        
        // Gérer les messages
        this.wsService.onMessage((data) => {
            console.log('📥 Received message:', data);
            // Mettre à jour l'état du jeu si présent dans le message
            if (data.state) {
                gameState.setState(data.state);
                // Mettre à jour les choix si présents
                if (data.state.choices) {
                    gameChoices.setAvailableChoices(data.state.choices);
                }
            }
            this.messageHandlers.forEach(handler => handler(data));
        });
    }

    async sendAction(action: string, data: any = {}): Promise<void> {
        if (!this.wsService) {
            throw new Error('WebSocket not initialized');
        }
        await this.wsService.sendAction(action, data);
    }

    async sendChoice(choice: Choice): Promise<void> {
        if (!this.wsService) {
            throw new Error('WebSocket not initialized');
        }

        // Mettre à jour le store avec le choix sélectionné
        gameChoices.selectChoice(choice);
        
        // Envoyer le choix au serveur
        await this.wsService.sendChoice(choice.text);
    }

    onMessage(handler: (data: GameResponse) => void): () => void {
        this.messageHandlers.push(handler);
        return () => {
            this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
        };
    }

    async disconnect(): Promise<void> {
        if (this.wsService) {
            this.wsService.disconnect();
            this.wsService = null;
        }
    }

    async reset(): Promise<void> {
        // Déconnecter le WebSocket
        await this.disconnect();
        
        try {
            // Appeler l'API de reset
            const response = await this.customFetch(`${this.API_BASE_URL}/reset`, {
                method: 'POST',
                credentials: 'include'
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Failed to reset game');
            }

            console.log('🔄 Game reset successful');
        } catch (error) {
            console.error('❌ Failed to reset game:', error);
            throw error;
        } finally {
            // Toujours effacer les cookies et l'état même si le reset échoue
            gameSession.clearSession();
            gameState.reset();
            gameChoices.reset();
        }
    }

    private messageHandlers: ((data: GameResponse) => void)[] = [];
}

export const gameService = new GameService();
