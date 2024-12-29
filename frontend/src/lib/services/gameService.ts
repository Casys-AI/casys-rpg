import type { GameState, GameResponse } from '$lib/types/game';
import { browser } from '$app/environment';
import { gameSession, gameState, gameChoices, type Choice } from '$lib/stores/gameStore';
import { WebSocketService, type ConnectionStatus } from './websocketService';
import { writable, type Writable } from 'svelte/store';

class GameService {
    private wsService: WebSocketService | null = null;
    private readonly API_BASE_URL = 'http://127.0.0.1:8000/api/game';
    private readonly WS_URL = 'ws://127.0.0.1:8000/api/ws/game';  
    private customFetch: typeof fetch = fetch;
    private messageHandlers: ((data: GameResponse) => void)[] = [];

    // Exposer le status de connexion du WebSocket
    get connectionStatus(): Writable<ConnectionStatus> {
        return this.wsService?.connectionStatus || writable<ConnectionStatus>('disconnected');
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
                body: JSON.stringify({})  // Envoyer un objet vide pour satisfaire FastAPI
            });

            const data = await response.json();
            console.log('🎲 Game initialized response:', data);
            
            if (!response.ok) {
                throw new Error(data.detail?.[0]?.msg || data.message || 'Server error');
            }
            
            if (data.success) {
                if (browser) {
                    // D'abord effacer la session existante et les états
                    gameSession.clearSession();
                    gameState.reset();
                    gameChoices.reset();
                    
                    // Stocker les nouveaux IDs
                    gameSession.setSession(data.state.session_id, data.state.game_id);
                    // Mettre à jour l'état du jeu
                    gameState.setState(data.state);
                    // Mettre à jour les choix si présents
                    if (data.state.choices) {
                        gameChoices.setAvailableChoices(data.state.choices);
                    }
                    await this.connectWebSocket();
                }
                return data;
            } 
            
            throw new Error(data.message || 'Failed to initialize game');
        } catch (error) {
            console.error('🎲 Game initialization error:', error);
            throw error;
        }
    }

    // Méthode publique pour se connecter au WebSocket
    async connectWebSocket(): Promise<void> {
        if (this.wsService) {
            console.log('🔌 WebSocket already connected');
            return;
        }

        console.log('🔌 Creating new WebSocket connection');
        this.wsService = new WebSocketService(this.WS_URL);
        
        // Gérer les messages
        this.wsService.onMessage(this.handleMessage.bind(this));
    }

    private handleMessage(data: GameResponse) {
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
    }

    async getGameState(): Promise<GameResponse> {
        console.log('🎲 Getting game state...');
        try {
            // Récupérer le game_id du store
            let currentGameId: string | null = null;
            gameSession.subscribe(session => {
                currentGameId = session.gameId;
            })();

            // Si pas de game_id, retourner une erreur
            if (!currentGameId) {
                console.log('❌ No game ID found');
                return {
                    success: false,
                    message: 'No game ID found',
                    session_id: null,
                    game_id: null,
                    state: {}
                };
            }

            const response = await this.customFetch(`${this.API_BASE_URL}/state?game_id=${currentGameId}`, {
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
}

export const gameService = new GameService();
