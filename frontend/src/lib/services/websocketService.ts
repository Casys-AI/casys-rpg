import { browser } from '$app/environment';
import { writable, type Writable } from 'svelte/store';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: ((data: any) => void)[] = [];
  private reconnectTimeout: number = 1000;
  private maxReconnectAttempts: number = 5;
  private reconnectAttempts: number = 0;
  private heartbeatInterval: number | null = null;

  // Store pour l'état de la connexion
  public connectionStatus: Writable<ConnectionStatus> = writable('disconnected');

  constructor(private wsUrl: string) {
    if (browser) {
      this.connect();
    }
  }

  private connect(): void {
    console.log(' Connecting to WebSocket...', this.wsUrl);
    this.connectionStatus.set('connecting');

    this.ws = new WebSocket(this.wsUrl);
    this.ws.onopen = () => this.onopen();
    this.ws.onmessage = (event) => this.onmessage(event);
    this.ws.onclose = () => this.onclose();
    this.ws.onerror = (error) => this.onerror(error);
  }

  private onopen(): void {
    console.log(' WebSocket connected');
    this.connectionStatus.set('connected');
    this.reconnectAttempts = 0;
    this.startHeartbeat();
  }

  private onmessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      
      // Gérer le heartbeat
      if (data.type === 'pong') {
        console.log(' Heartbeat received');
        return;
      }

      console.log(' Received message:', data);
      this.messageHandlers.forEach(handler => handler(data));
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  private onclose(): void {
    console.log(' WebSocket disconnected');
    this.connectionStatus.set('disconnected');
    this.stopHeartbeat();
    this.handleReconnect();
  }

  private onerror(error: Event): void {
    console.error(' WebSocket error:', error);
    this.connectionStatus.set('error');
  }

  private handleReconnect(): void {
    if (!browser) return; // Ne pas tenter de reconnexion côté serveur
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(' Max reconnection attempts reached');
      return;
    }

    const timeout = this.reconnectTimeout * Math.pow(2, this.reconnectAttempts);
    console.log(` Attempting to reconnect in ${timeout}ms (attempt ${this.reconnectAttempts + 1})`);

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, timeout);
  }

  private startHeartbeat(): void {
    if (!browser) return; // Ne pas démarrer le heartbeat côté serveur
    console.log(' Starting heartbeat');
    this.stopHeartbeat();
    
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        console.log(' Sending heartbeat');
        this.send({ type: 'ping' });
      }
    }, 30000); // Ping toutes les 30 secondes
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      console.log(' Stopping heartbeat');
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  async send(data: any): Promise<void> {
    if (!browser) return; // Ne pas envoyer de messages côté serveur
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    console.log(' Sending message:', data);
    this.ws.send(JSON.stringify(data));
  }

  async sendAction(action: string, data: any = {}): Promise<void> {
    console.log(' Sending action:', { action, ...data });
    await this.send({ action, ...data });
  }

  async sendChoice(choice: string): Promise<void> {
    console.log(' Sending choice:', choice);
    
    // Attendre que la connexion soit établie
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.log(' WebSocket not ready, connecting...');
      this.connect();
    }
    
    // Vérifier à nouveau l'état de la connexion
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket connection failed');
    }
    
    await this.send({ type: 'choice', choice });
  }

  onMessage(handler: (data: any) => void): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  disconnect(): void {
    if (!browser) return; // Ne pas déconnecter côté serveur
    console.log(' Disconnecting WebSocket...');
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionStatus.set('disconnected');
  }
}
