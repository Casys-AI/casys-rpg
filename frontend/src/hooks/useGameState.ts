import { $, useSignal, useTask$, useVisibleTask$ } from '@builder.io/qwik';
import { gameStateWS } from '~/services/api';
import type { GameState } from '~/types/game';

export const useGameState = () => {
  const gameState = useSignal<GameState | null>(null);
  const error = useSignal<string | null>(null);
  const isConnected = useSignal(false);

  // Initialiser la connexion WebSocket
  useVisibleTask$(() => {
    const listener = {
      onStateUpdate: (state: GameState) => {
        gameState.value = state;
        error.value = null;
        isConnected.value = true;
      },
      onError: (err: Error) => {
        error.value = err.message;
        isConnected.value = false;
      }
    };

    gameStateWS.addListener(listener);
    gameStateWS.connect();

    // Cleanup lors du démontage
    return () => {
      gameStateWS.removeListener(listener);
      gameStateWS.disconnect();
    };
  });

  // Fonction pour reconnecter manuellement
  const reconnect = $(() => {
    gameStateWS.connect();
  });

  return {
    gameState,
    error,
    isConnected,
    reconnect
  };
};
