import type { GameState, GameResponse } from '$lib/types/game';
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

class GameService {
    private ws: WebSocket | null = null;
    private messageHandlers: ((data: GameResponse) => void)[] = [];
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectTimeout = 1000;
    private heartbeatInterval: number | null = null;
    private customFetch: typeof fetch = fetch;
    
    // Store pour l'état de la connexion
    public connectionStatus = writable<ConnectionStatus>('disconnected');
    
    setFetch(fetchFn: typeof fetch) {
        this.customFetch = fetchFn;
    }
    
    async initialize(): Promise<GameResponse> {
        console.log('🎮 Initializing game...');
        this.connectionStatus.set('connecting');
        const response = await this.customFetch('/api/game/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        const data = await response.json();
        console.log('🎲 Game initialized:', data);
        
        if (data.success && browser) {
            await this.connectWebSocket();
        } else if (!data.success) {
            this.connectionStatus.set('error');
        }
        return data;
    }

    async getGameState(): Promise<GameResponse> {
        console.log('🎲 Getting game state...');
        try {
            const response = await this.customFetch('/api/game/state', {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                console.log('❌ No session found');
                return {
                    success: false,
                    message: 'No session found',
                    session_id: null,
                    game_id: null
                };
            }

            const data = await response.json();
            console.log('📥 Got game state:', data);
            return {
                ...data,
                success: true
            };
        } catch (error) {
            console.error('❌ Failed to get game state:', error);
            return {
                success: false,
                message: error instanceof Error ? error.message : 'Failed to get game state',
                session_id: null,
                game_id: null
            };
        }
    }

    private async connectWebSocket() {
        if (!browser) return; // Ne pas se connecter côté serveur
        if (this.ws?.readyState === WebSocket.OPEN) return;

        console.log('🔌 Connecting to WebSocket...');
        this.connectionStatus.set('connecting');
        
        // Utiliser l'URL du backend
        const wsUrl = `ws://${window.location.hostname}:8000/api/ws/game`;
        console.log('🔌 WebSocket URL:', wsUrl);
        
        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'pong') {
                    console.log('❤️ Heartbeat received');
                    return;
                }
                console.log('📥 Received state:', data);
                this.messageHandlers.forEach(handler => handler(data));
            };

            this.ws.onopen = this.onopen.bind(this);
            this.ws.onclose = this.onclose.bind(this);
            this.ws.onerror = this.onerror.bind(this);

            await new Promise((resolve, reject) => {
                if (!this.ws) return reject(new Error('WebSocket not initialized'));

                resolve(true);
            });
        } catch (error) {
            console.error('❌ Error connecting to WebSocket:', error);
            this.connectionStatus.set('error');
            this.handleReconnect();
        }
    }

    private onopen() {
        console.log('🔌 WebSocket connected');
        this.connectionStatus.set('connected');
        this.reconnectAttempts = 0;
        this.startHeartbeat();
    }

    private onclose() {
        console.log('🔌 WebSocket disconnected');
        this.connectionStatus.set('disconnected');
        this.clearHeartbeat();
        this.handleReconnect();
    }

    private onerror(error: Event) {
        console.error('❌ WebSocket error:', error);
        this.connectionStatus.set('error');
    }

    private startHeartbeat() {
        if (!browser) return; // Ne pas démarrer le heartbeat côté serveur
        console.log('❤️ Starting heartbeat');
        this.clearHeartbeat();
        this.heartbeatInterval = window.setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                console.log('❤️ Sending heartbeat');
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Ping toutes les 30 secondes
    }

    private clearHeartbeat() {
        if (this.heartbeatInterval) {
            console.log('❤️ Stopping heartbeat');
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    private async handleReconnect() {
        if (!browser) return; // Ne pas tenter de reconnexion côté serveur
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('🔌 Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const timeout = this.reconnectTimeout * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`🔄 Attempting to reconnect in ${timeout}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => this.connectWebSocket(), timeout);
    }

    onMessage(handler: (data: GameResponse) => void) {
        this.messageHandlers.push(handler);
        return () => {
            this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
        };
    }

    async sendAction(action: string, data: any = {}) {
        if (!browser) return; // Ne pas envoyer d'actions côté serveur
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('❌ WebSocket not connected');
            throw new Error('WebSocket not connected');
        }

        console.log('📤 Sending action:', { action, ...data });
        this.ws.send(JSON.stringify({ action, ...data }));
    }

    async sendChoice(choice: string) {
        console.log('📤 Sending choice via WebSocket:', choice);
        
        // Attendre que la connexion soit établie
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.log('⏳ WebSocket not ready, connecting...');
            await this.connectWebSocket();
        }
        
        // Vérifier à nouveau l'état de la connexion
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket connection failed');
        }
        
        const message = { 
            type: 'choice',
            choice: choice 
        };
        console.log('📦 Sending message:', message);
        this.ws.send(JSON.stringify(message));
    }

    disconnect() {
        if (!browser) return; // Ne pas déconnecter côté serveur
        console.log('🔌 Disconnecting...');
        this.clearHeartbeat();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

export const gameService = new GameService();
