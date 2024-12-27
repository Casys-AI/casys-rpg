import { $, useSignal, useVisibleTask$, noSerialize } from '@builder.io/qwik';
import { API_CONFIG } from '~/config/api';

export interface GameState {
  session_id: string;
  game_id: string;
  section_number: number;
}

export function useGameState() {
  const gameState = useSignal<GameState | null>(null);
  const socket = useSignal<any>(null);
  const error = useSignal<string | null>(null);
  const isConnecting = useSignal<boolean>(false);

  // Fonction utilitaire pour gérer les messages WebSocket
  const handleWebSocketMessage = $((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      gameState.value = data;
    } catch (err) {
      console.error('WebSocket message error:', err);
    }
  });

  // Fonction utilitaire pour gérer les erreurs WebSocket
  const handleWebSocketError = $((event: Event) => {
    console.error('WebSocket error:', event);
    error.value = 'WebSocket connection error';
  });

  // Configuration du WebSocket
  const setupWebSocket = $(async () => {
    if (socket.value?.readyState === WebSocket.OPEN || isConnecting.value) {
      return;
    }

    try {
      isConnecting.value = true;
      const wsUrl = `${API_CONFIG.WS_URL}${API_CONFIG.WS_ENDPOINT}`;
      console.log('Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => handleWebSocketMessage(event);
      ws.onerror = (event) => handleWebSocketError(event);
      ws.onclose = () => {
        console.log('WebSocket closed');
        socket.value = null;
        isConnecting.value = false;
        // Tentative de reconnexion après 5 secondes
        setTimeout(async () => {
          await setupWebSocket();
        }, 5000);
      };
      
      // Utiliser noSerialize pour l'objet WebSocket
      socket.value = noSerialize(ws);
    } catch (err) {
      console.error('WebSocket setup error:', err);
      error.value = 'Failed to setup WebSocket';
    } finally {
      isConnecting.value = false;
    }
  });

  // Initialiser une nouvelle partie
  const initializeGame = $(async () => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/game/initialize`, {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS
      });

      if (!response.ok) {
        throw new Error('Failed to initialize game');
      }

      const data = await response.json();
      gameState.value = data;
      
      // S'assurer que le WebSocket est connecté
      await setupWebSocket();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
    }
  });

  // Établir la connexion WebSocket au chargement
  useVisibleTask$(async () => {
    await setupWebSocket();
    
    return () => {
      if (socket.value) {
        socket.value.close();
      }
    };
  });

  return {
    gameState,
    error,
    initializeGame,
  };
}
