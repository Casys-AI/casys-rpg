import { $, useSignal, useStore, useTask$ } from '@builder.io/qwik';
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

/**
 * Hook principal de gestion du jeu
 */
export const useGame = () => {
  console.log(' [useGame] Initializing hook');
  
  const location = useLocation();
  
  // Signaux WebSocket
  const wsConnected = useSignal(false);
  const wsError = useSignal<string | null>(null);

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

  // Actions du jeu
  const actions = {
    /**
     * Initialise le jeu avec un état optionnel
     */
    initGame: $(async (initialState?: GameState) => {
      console.log(' [useGame] Starting game initialization');
      try {
        // Si on a un état initial, on l'utilise
        if (initialState) {
          console.log(' [useGame] Using provided initial state');
          store.state = initialState;
        } else {
          console.log(' [useGame] Fetching game state from server');
          // Sinon on charge depuis le serveur
          const newState = await gameService.getGameState();
          console.log(' [useGame] Received state:', newState);
          store.sessionId = newState.sessionId;
          store.gameId = newState.gameId;
          store.state = newState;
        }

        console.log(' [useGame] Game initialized successfully');
        return store.state;
      } catch (error) {
        console.error(' [useGame] Initialization error:', error);
        throw error;
      }
    }),

    /**
     * Navigation entre les sections
     */
    navigate: $(async (section: number) => {
      console.log(' [useGame] Navigating to section:', section);
      try {
        if (!websocketService.isConnected()) {
          throw new Error('WebSocket non connecté');
        }

        const message = {
          type: 'navigate',
          data: { section }
        };

        websocketService.send(message);
      } catch (error) {
        console.error(' [useGame] Navigation error:', error);
        store.error = error instanceof Error ? error.message : 'Erreur de navigation';
      }
    }),

    /**
     * Lance les dés
     */
    rollDice: $(async (diceType: string): Promise<number> => {
      console.log(' [useGame] Rolling dice:', diceType);
      try {
        if (!store.sessionId || !store.gameId) {
          throw new Error('Session invalide');
        }

        return await gameService.rollDice(store.sessionId, store.gameId, diceType);
      } catch (error) {
        console.error(' [useGame] Dice roll error:', error);
        store.error = error instanceof Error ? error.message : 'Erreur de lancer de dés';
        return 0;
      }
    }),

    /**
     * Efface les erreurs
     */
    clearError: $(() => {
      console.log(' [useGame] Clearing errors');
      store.error = null;
      wsError.value = null;
    })
  };

  // Task pour la gestion WebSocket
  useTask$(({ track, cleanup }) => {
    console.log(' [useGame] Setting up WebSocket task');
    track(() => store.sessionId);
    track(() => store.gameId);
    
    if (store.sessionId && store.gameId && !websocketService.isConnected()) {
      console.log(' [useGame] Connecting WebSocket');
      websocketService.connect({
        onMessage$: $((data: any) => {
          console.log(' [useGame] WebSocket message:', data);
          if (data.type === 'state') {
            store.state = data.state;
          }
        }),
        onError$: $((error: any) => {
          console.error(' [useGame] WebSocket error:', error);
          wsError.value = error instanceof Error ? error.message : 'Erreur de connexion';
        }),
        onClose$: $(() => {
          console.log(' [useGame] WebSocket closed');
          wsConnected.value = false;
        })
      });
      wsConnected.value = true;
    }

    // Nettoyage
    cleanup(() => {
      console.log(' [useGame] Cleaning up WebSocket');
      if (websocketService.isConnected()) {
        websocketService.disconnect();
        wsConnected.value = false;
      }
    });
  });

  return {
    store,
    wsConnected: wsConnected.value,
    wsError: wsError.value,
    actions
  };
};
