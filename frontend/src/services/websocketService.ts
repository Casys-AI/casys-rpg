import type { QRL } from '@builder.io/qwik';
import { API_CONFIG, buildWsUrl } from '../config/api';

export interface WebSocketHandlers {
  onMessage$: QRL<(data: any) => void>;
  onError$: QRL<(error: Error) => void>;
  onClose$: QRL<() => void>;
}

let wsInstance: WebSocket | null = null;

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
  connect: (handlers: WebSocketHandlers): void => {
    if (wsInstance?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsInstance = new WebSocket(buildWsUrl());
      
      wsInstance.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          await handlers.onMessage$(data);
        } catch (error) {
          await handlers.onError$(new Error('Erreur de parsing des données'));
        }
      };

      wsInstance.onerror = async () => {
        await handlers.onError$(new Error('Erreur de connexion WebSocket'));
      };

      wsInstance.onclose = async () => {
        wsInstance = null;
        await handlers.onClose$();
      };

    } catch (error) {
      handlers.onError$(new Error('Erreur d\'initialisation WebSocket'));
    }
  },

  /**
   * Envoie un message via WebSocket
   */
  send: (data: unknown): void => {
    if (wsInstance?.readyState === WebSocket.OPEN) {
      wsInstance.send(JSON.stringify(data));
    }
  },

  /**
   * Ferme la connexion WebSocket
   */
  disconnect: (): void => {
    if (wsInstance?.readyState === WebSocket.OPEN) {
      wsInstance.close();
      wsInstance = null;
    }
  }
};
