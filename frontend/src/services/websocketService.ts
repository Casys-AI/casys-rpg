import type { QRL } from '@builder.io/qwik';
import { API_CONFIG, buildWsUrl } from '../config/api';

export interface WebSocketHandlers {
  onMessage$?: QRL<(data: any) => void>;
  onError$?: QRL<(error: Error) => void>;
  onClose$?: QRL<() => void>;
}

interface WebSocketMessage {
  type: string;
  data: any;
}

let wsInstance: WebSocket | null = null;
let messageQueue: WebSocketMessage[] = [];
let isConnecting = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;

/**
 * Service WebSocket
 * Gère l'instance WebSocket en interne pour éviter les problèmes de sérialisation
 */
export const websocketService = {
  /**
   * Vérifie si la connexion est active
   */
  isConnected: () => wsInstance?.readyState === WebSocket.OPEN,

  /**
   * Crée une nouvelle connexion WebSocket
   */
  connect: async (handlers?: WebSocketHandlers): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (wsInstance?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (isConnecting) {
        reject(new Error('Connexion en cours'));
        return;
      }

      try {
        isConnecting = true;
        wsInstance = new WebSocket(buildWsUrl());
        
        wsInstance.onopen = () => {
          console.log(' [WebSocket] Connected');
          isConnecting = false;
          reconnectAttempts = 0;
          
          // Envoyer les messages en attente
          while (messageQueue.length > 0) {
            const message = messageQueue.shift();
            if (message && wsInstance?.readyState === WebSocket.OPEN) {
              wsInstance.send(JSON.stringify(message));
            }
          }
          
          resolve();
        };

        wsInstance.onmessage = async (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log(' [WebSocket] Message received:', data);
            if (handlers?.onMessage$) {
              await handlers.onMessage$(data);
            }
          } catch (error) {
            console.error(' [WebSocket] Error parsing message:', error);
          }
        };

        wsInstance.onerror = async (event) => {
          console.error(' [WebSocket] Error:', event);
          if (handlers?.onError$) {
            await handlers.onError$(new Error('WebSocket error'));
          }
        };

        wsInstance.onclose = async () => {
          console.log(' [WebSocket] Closed');
          wsInstance = null;

          if (handlers?.onClose$) {
            await handlers.onClose$();
          }

          // Tentative de reconnexion
          if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(() => {
              websocketService.connect(handlers);
            }, 1000 * reconnectAttempts);
          }
        };
      } catch (error) {
        console.error(' [WebSocket] Connection error:', error);
        isConnecting = false;
        reject(error);
      }
    });
  },

  /**
   * Envoie un message via WebSocket
   */
  send: (data: WebSocketMessage): void => {
    if (wsInstance?.readyState === WebSocket.OPEN) {
      wsInstance.send(JSON.stringify(data));
    } else {
      console.log(' [WebSocket] Queuing message:', data);
      messageQueue.push(data);
    }
  },

  /**
   * Ferme la connexion WebSocket
   */
  disconnect: (): void => {
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }
    messageQueue = [];
    isConnecting = false;
    reconnectAttempts = 0;
  }
};
