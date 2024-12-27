import { useSignal, useStore, useTask$, $ } from '@builder.io/qwik';
import { useLocation } from '@builder.io/qwik-city';
import { gameService } from '../services/gameService';
import { websocketService } from '../services/websocketService';
import type { GameState } from '../types/game';

export interface GameStore {
  sessionId: string | null;
  gameId: string | null;
  state: GameState | null;
  isLoading: boolean;
  error: string | null;
  currentRoute: string;
}

interface WebSocketMessage {
  type: string;
  state?: GameState;
  error?: string;
  data?: any;
}

/**
 * Hook principal de gestion du jeu
 */
export const useGame = () => {
  console.log(' [useGame] Initializing hook');
  
  const location = useLocation();
  
  // Signaux
  const wsConnected = useSignal(false);
  const wsError = useSignal<string | null>(null);
  const isInitializing = useSignal(false);
  const isNavigating = useSignal(false);
  const isRollingDice = useSignal(false);

  // Store principal
  const store = useStore<GameStore>({
    sessionId: null,
    gameId: null,
    state: null,
    isLoading: false,
    error: null,
    currentRoute: location.url.pathname
  });

  console.log(' [useGame] Initial store state:', store);

  // Gestionnaires WebSocket
  const handleMessage = $(async (data: unknown) => {
    console.log(' [useGame] WebSocket message:', data);
    if (data && typeof data === 'object' && 'type' in data) {
      const message = data as WebSocketMessage;
      if (message.type === 'state' && message.state) {
        store.state = message.state;
      }
    }
  });

  const handleError = $(async (error: any) => {
    console.error(' [useGame] WebSocket error:', error);
    wsError.value = error instanceof Error ? error.message : 'Erreur de connexion';
    wsConnected.value = false;
  });

  const handleClose = $(async () => {
    console.log(' [useGame] WebSocket closed');
    wsConnected.value = false;
  });

  // Fonction utilitaire pour assurer la connexion WebSocket
  const ensureWebSocketConnection = $(async () => {
    if (!websocketService.isConnected()) {
      try {
        await websocketService.connect({
          onMessage$: handleMessage,
          onError$: handleError,
          onClose$: handleClose
        });
        wsConnected.value = true;
        wsError.value = null;
      } catch (error) {
        console.error(' [useGame] WebSocket connection error:', error);
        wsError.value = error instanceof Error ? error.message : 'Erreur de connexion';
        wsConnected.value = false;
        throw error;
      }
    }
  });

  // Actions
  const initGame = $(async (initialState?: GameState) => {
    console.log(' [useGame] Starting game initialization');
    isInitializing.value = true;
    try {
      if (initialState) {
        console.log(' [useGame] Using provided initial state');
        store.state = initialState;
      } else {
        console.log(' [useGame] Fetching game state from server');
        const newState = await gameService.getGameState();
        console.log(' [useGame] Received state:', newState);
        store.sessionId = newState.sessionId;
        store.gameId = newState.gameId;
        store.state = newState;
      }

      // Établir la connexion WebSocket après l'initialisation
      await ensureWebSocketConnection();

      console.log(' [useGame] Game initialized successfully');
      return store.state;
    } catch (error) {
      console.error(' [useGame] Initialization error:', error);
      throw error;
    } finally {
      isInitializing.value = false;
    }
  });

  const navigate = $(async (section: number) => {
    console.log(' [useGame] Navigating to section:', section);
    isNavigating.value = true;
    try {
      // S'assurer que la connexion WebSocket est établie
      await ensureWebSocketConnection();

      const message = {
        type: 'navigate',
        data: { section }
      };

      websocketService.send(message);
    } catch (error) {
      console.error(' [useGame] Navigation error:', error);
      store.error = error instanceof Error ? error.message : 'Erreur de navigation';
    } finally {
      isNavigating.value = false;
    }
  });

  const rollDice = $(async (diceType: string): Promise<number> => {
    console.log(' [useGame] Rolling dice:', diceType);
    isRollingDice.value = true;
    try {
      if (!store.sessionId || !store.gameId) {
        throw new Error('Session invalide');
      }

      // S'assurer que la connexion WebSocket est établie
      await ensureWebSocketConnection();

      return await gameService.rollDice(store.sessionId, store.gameId, diceType);
    } catch (error) {
      console.error(' [useGame] Dice roll error:', error);
      store.error = error instanceof Error ? error.message : 'Erreur de lancer de dés';
      return 0;
    } finally {
      isRollingDice.value = false;
    }
  });

  const clearError = $(async () => {
    console.log(' [useGame] Clearing errors');
    store.error = null;
    wsError.value = null;
  });

  // Task pour la gestion WebSocket
  useTask$(({ track, cleanup }) => {
    console.log(' [useGame] Setting up WebSocket task');
    track(() => store.sessionId);
    track(() => store.gameId);
    
    if (store.sessionId && store.gameId) {
      ensureWebSocketConnection().catch(error => {
        console.error(' [useGame] WebSocket setup error:', error);
      });
    }

    // Nettoyage
    cleanup(() => {
      console.log(' [useGame] Cleaning up WebSocket');
      websocketService.disconnect();
    });
  });

  return {
    store,
    wsConnected: wsConnected.value,
    wsError: wsError.value,
    isInitializing: isInitializing.value,
    isNavigating: isNavigating.value,
    isRollingDice: isRollingDice.value,
    actions: {
      initGame,
      navigate,
      rollDice,
      clearError
    }
  };
};
