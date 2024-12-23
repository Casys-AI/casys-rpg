import { $, useSignal, useTask$ } from '@builder.io/qwik';
import { gameStateWS } from '~/services/api';
import type { GameState } from '~/types/game';

export const useGameState = () => {
  const gameState = useSignal<GameState | null>(null);
  const error = useSignal<string | null>(null);
  const isConnected = useSignal(false);

  // Initialiser la connexion WebSocket de manière non-bloquante
  useTask$(({ track, cleanup }) => {
    // Track pour réexécuter si ces valeurs changent
    track(() => isConnected.value);
    
    const listener = {
      onStateUpdate: (state: GameState | null) => {
        if (state === null) {
          // C'est juste un signal de connexion réussie
          error.value = null;
          isConnected.value = true;
          return;
        }
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
    cleanup(() => {
      gameStateWS.removeListener(listener);
      gameStateWS.disconnect();
    });
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
