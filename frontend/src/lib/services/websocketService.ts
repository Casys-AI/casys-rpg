import { browser } from '$app/environment';
import { writable, get, type Writable } from 'svelte/store';
import type { Choice } from '$lib/types/game';
import { gameState } from '$lib/stores/gameStore';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: ((data: any) => void)[] = [];
  private reconnectTimeout: number = 1000;
  private maxReconnectAttempts: number = 5;
  private reconnectAttempts: number = 0;
  private heartbeatInterval: number | null = null;
  private maxReconnectDelay: number = 30000;

  // Store pour l'état de la connexion
  public connectionStatus: Writable<ConnectionStatus> = writable('disconnected');

  constructor(private wsUrl: string, autoConnect: boolean = true) {
    if (browser && autoConnect) {
      this.connect();
    }
  }

  public connect(): void {
    console.log('🔌 Connecting to WebSocket...', this.wsUrl);
    this.connectionStatus.set('connecting');

    this.ws = new WebSocket(this.wsUrl);
    this.ws.onopen = this.onopen.bind(this);
    this.ws.onmessage = this.onmessage.bind(this);
    this.ws.onclose = this.onclose.bind(this);
    this.ws.onerror = this.onerror.bind(this);
  }

  private onopen(): void {
    console.log('🔌 WebSocket connected');
    this.connectionStatus.set('connected');
    this.reconnectAttempts = 0;
    this.startHeartbeat();
  }

  private onmessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      
      // Gérer le heartbeat
      if (data.type === 'pong') {
        console.log('❤️ Heartbeat received');
        return;
      }

      console.log('📥 Received message:', data);
      this.messageHandlers.forEach(handler => handler(data));
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  private onclose(): void {
    console.log('🔌 WebSocket disconnected');
    this.connectionStatus.set('disconnected');
    this.stopHeartbeat();
    this.handleReconnect();
  }

  private onerror(error: Event): void {
    console.error('❌ WebSocket error:', error);
    this.connectionStatus.set('error');
  }

  private handleReconnect(): void {
    if (!browser) return; // Ne pas tenter de reconnexion côté serveur
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('🔌 Max reconnection attempts reached');
      return;
    }

    const timeout = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);
    console.log(`🔄 Attempting to reconnect in ${timeout}ms (attempt ${this.reconnectAttempts + 1})`);

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, timeout);
  }

  private startHeartbeat(): void {
    console.log('❤️ Starting heartbeat');
    this.stopHeartbeat();
    
    // Vérifier si on est dans un environnement browser
    if (browser) {
      this.heartbeatInterval = window.setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          console.log('❤️ Sending heartbeat');
          this.send({ type: 'ping' });
        }
      }, 30000); // 30 secondes
    }
  }

  private stopHeartbeat(): void {
    if (browser && this.heartbeatInterval) {
      window.clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  public async disconnect(): Promise<void> {
    if (this.ws) {
      this.ws.close();
      this.connectionStatus.set('disconnected');
      
      if (browser && this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }
    }
  }

  private async send(message: any): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }
    this.ws.send(JSON.stringify(message));
  }

  public async sendAction(action: string, data: any = {}): Promise<void> {
    await this.send({ action, ...data });
  }

  public async sendChoice(choice: Choice): Promise<void> {
    if (!this.ws || get(this.connectionStatus) !== 'connected') {
      throw new Error('WebSocket not connected');
    }

    const currentGameState = get(gameState);
    if (!currentGameState?.game_id) {
      throw new Error('No game ID available');
    }

    console.log('📤 Sending choice:', choice);
    const message = {
      type: 'choice',
      choice: {
        game_id: currentGameState.game_id,
        choice_id: String(choice.target_section),
        choice_text: choice.text,
        metadata: {
          type: choice.type,
          target_section: choice.target_section,
          conditions: choice.conditions,
          dice_type: choice.dice_type,
          dice_results: choice.dice_results
        }
      }
    };

    try {
      await this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending choice:', error);
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
