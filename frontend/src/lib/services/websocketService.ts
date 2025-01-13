import { browser } from '$app/environment';
import { writable, get, type Writable } from 'svelte/store';
import type { GameResponse } from '$lib/types/game';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: ((data: any) => void)[] = [];
  private heartbeatInterval: number | null = null;
  private messageQueue: any[] = [];
  private isConnecting: boolean = false;
  private reconnectTimeout: number | null = null;

  // Store pour l'état de la connexion
  public connectionStatus: Writable<ConnectionStatus> = writable('disconnected');

  constructor(private wsUrl: string, autoConnect: boolean = true) {
    if (browser && autoConnect) {
      this.connect();
    }
  }

  public async connect(): Promise<void> {
    if (!browser || this.isConnecting) return;

    this.isConnecting = true;
    console.log('🔌 Connecting to WebSocket...', this.wsUrl);
    this.connectionStatus.set('connecting');

    try {
      // Créer la connexion WebSocket
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('🟢 WebSocket connected');
        this.connectionStatus.set('connected');
        this.startHeartbeat();
        this.processMessageQueue();
        this.isConnecting = false;
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = null;
        }
      };

      this.ws.onclose = () => {
        console.log('🔴 WebSocket disconnected');
        this.connectionStatus.set('disconnected');
        this.stopHeartbeat();
        this.isConnecting = false;
        this.ws = null;

        // Tentative de reconnexion après 1 seconde
        if (!this.reconnectTimeout) {
          this.reconnectTimeout = window.setTimeout(() => {
            console.log('🔄 Attempting to reconnect...');
            this.connect();
          }, 1000);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.connectionStatus.set('error');
        this.isConnecting = false;
      };

      this.ws.onmessage = (event) => {
        try {
          console.log('📥 Raw WebSocket message:', event.data);
          const data = JSON.parse(event.data);
          console.log('📥 Parsed message:', data);
          
          // Gérer le heartbeat ici
          if (data.type === 'pong') {
            console.log('❤️ Heartbeat received');
            return;
          }
          
          // Notifier tous les handlers enregistrés uniquement pour les messages non-heartbeat
          this.messageHandlers.forEach(handler => handler(data));
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error, 'Raw message:', event.data);
        }
      };

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.connectionStatus.set('error');
      this.isConnecting = false;
    }
  }

  private async processMessageQueue(): Promise<void> {
    console.log('📤 Processing message queue:', this.messageQueue.length, 'messages');
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      try {
        await this.send(message, false);
      } catch (error) {
        console.error('Error sending queued message:', error);
        // Remettre le message dans la file si erreur
        this.messageQueue.unshift(message);
        break;
      }
    }
  }

  private startHeartbeat(): void {
    console.log('❤️ Starting heartbeat');
    this.stopHeartbeat();
    
    if (browser) {
      this.heartbeatInterval = window.setInterval(() => {
        this.send({ type: 'ping' }, false).catch(error => {
          console.error('Error sending heartbeat:', error);
        });
      }, 30000);
    }
  }

  private stopHeartbeat(): void {
    if (browser && this.heartbeatInterval) {
      window.clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  public async disconnect(): Promise<void> {
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionStatus.set('disconnected');
  }

  public async send(message: any, queue: boolean = true): Promise<void> {
    const status = get(this.connectionStatus);
    
    if (status !== 'connected' || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (queue) {
        console.log('📥 Queuing message:', message);
        this.messageQueue.push(message);
        
        if (status === 'disconnected') {
          console.log('🔄 Reconnecting WebSocket...');
          await this.connect();
        }
        return;
      }
      throw new Error(`WebSocket not connected (status: ${status})`);
    }

    try {
      console.log('📤 Sending message:', message);
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending message:', error);
      if (queue) {
        console.log('📥 Queuing failed message:', message);
        this.messageQueue.push(message);
      }
      throw error;
    }
  }

  onMessage(handler: (data: any) => void): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  public getConnectionStatus(): ConnectionStatus {
    return get(this.connectionStatus);
  }
}

// Export d'une instance unique du service
export const websocketService = new WebSocketService('ws://127.0.0.1:8000/api/ws/game');
