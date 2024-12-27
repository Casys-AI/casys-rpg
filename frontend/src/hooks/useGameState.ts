import { $, useSignal, useTask$, useVisibleTask$ } from '@builder.io/qwik';
import { gameStateWS, api } from '~/services/api';
import type { GameState } from '~/types/game';

export const useGameState = () => {
  const gameState = useSignal<GameState | null>(null);
  const error = useSignal<string | null>(null);
  const isConnected = useSignal(false);
  const isInitialized = useSignal(false);

  // Initialiser l'état du jeu
  useVisibleTask$(async ({ track }) => {
    track(() => isConnected.value);
    
    if (!isInitialized.value) {
      try {
        // Initialiser le jeu d'abord
        const initialState = await api.getGameState();
        if (initialState) {
          console.log('Initial state received:', initialState);
          gameState.value = initialState;
          isInitialized.value = true;
        } else {
          console.log('No initial state received, initializing game...');
          // Si pas d'état initial, initialiser le jeu
          const response = await fetch(`${api.API_BASE_URL}/api/game/initialize`, {
            method: 'POST'
          });
          const initData = await response.json();
          console.log('Game initialized:', initData);
          
          if (initData?.initial_state) {
            gameState.value = initData.initial_state;
            isInitialized.value = true;
          }
        }
      } catch (err) {
        console.error('Error initializing game state:', err);
        error.value = err instanceof Error ? err.message : 'Error initializing game state';
      }
    }
  });

  // Gérer la connexion WebSocket
  useTask$(({ track, cleanup }) => {
    track(() => isConnected.value);
    
    const listener = {
      onStateUpdate: (state: GameState | null) => {
        if (state === null) {
          // Signal de connexion réussie
          error.value = null;
          isConnected.value = true;
          return;
        }
        
        // Mise à jour de l'état avec validation
        if (state.narrative && typeof state.narrative === 'object') {
          console.log('Updating game state with:', state);
          gameState.value = state;
          error.value = null;
          isConnected.value = true;
        } else {
          console.error('Invalid game state received:', state);
        }
      },
      onError: (err: Error) => {
        console.error('WebSocket error:', err);
        error.value = err.message;
        isConnected.value = false;
      }
    };

    gameStateWS.addListener(listener);
    
    if (!isConnected.value) {
      gameStateWS.connect();
    }

    cleanup(() => {
      gameStateWS.removeListener(listener);
      gameStateWS.disconnect();
    });
  });

  // Fonction pour reconnecter manuellement
  const reconnect = $(async () => {
    try {
      await gameStateWS.connect();
      if (!gameState.value) {
        const initialState = await api.getGameState();
        if (initialState) {
          gameState.value = initialState;
        }
      }
    } catch (err) {
      console.error('Error reconnecting:', err);
      error.value = err instanceof Error ? err.message : 'Error reconnecting';
    }
  });

  return {
    gameState,
    error,
    isConnected,
    reconnect
  };
};
