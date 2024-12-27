import type { QRL } from '@builder.io/qwik';
import { API_CONFIG, buildWsUrl } from '../config/api';

export interface WebSocketHandlers {
  onMessage$: QRL<(data: any) => void>;
  onError$: QRL<(error: Error) => void>;
  onClose$: QRL<() => void>;
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
  connect: (handlers: WebSocketHandlers): Promise<void> => {
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
          isConnecting = false;
          reconnectAttempts = 0;
          
          // Envoyer les messages en attente
          while (messageQueue.length > 0) {
            const message = messageQueue.shift();
            if (message) {
              websocketService.send(message);
            }
          }
          
          resolve();
        };

        wsInstance.onmessage = async (event) => {
          try {
            const data = JSON.parse(event.data);
            await handlers.onMessage$(data);
          } catch (error) {
            await handlers.onError$(new Error('Erreur de parsing des données'));
          }
        };

        wsInstance.onerror = async () => {
          const error = new Error('Erreur de connexion WebSocket');
          await handlers.onError$(error);
          reject(error);
        };

        wsInstance.onclose = async () => {
          isConnecting = false;
          wsInstance = null;

          // Tentative de reconnexion si nécessaire
          if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(() => {
              websocketService.connect(handlers);
            }, 1000 * reconnectAttempts);
          }

          await handlers.onClose$();
        };

      } catch (error) {
        isConnecting = false;
        const wsError = new Error('Erreur d\'initialisation WebSocket');
        handlers.onError$(wsError);
        reject(wsError);
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
      // Mettre le message en file d'attente si la connexion n'est pas établie
      messageQueue.push(data);
      
      // Si pas de connexion en cours, tenter de se connecter
      if (!isConnecting && !wsInstance) {
        websocketService.connect({
          onMessage$: async () => {},
          onError$: async () => {},
          onClose$: async () => {}
        });
      }
    }
  },

  /**
   * Ferme la connexion WebSocket
   */
  disconnect: (): void => {
    messageQueue = [];
    reconnectAttempts = MAX_RECONNECT_ATTEMPTS; // Empêcher la reconnexion automatique
    
    if (wsInstance?.readyState === WebSocket.OPEN) {
      wsInstance.close();
      wsInstance = null;
    }
  }
};
