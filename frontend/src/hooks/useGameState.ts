import { $, useSignal, useTask$ } from '@builder.io/qwik';
import { isBrowser } from '@builder.io/qwik/build';
import { API_CONFIG, buildUrl, buildWsUrl } from '~/config/api';
import type { GameState } from '~/types/game';

export const useGameState = () => {
  const gameState = useSignal<GameState | null>(null);
  const error = useSignal<string | null>(null);
  const isConnected = useSignal(false);
  const shouldReconnect = useSignal(true);
  const isInitializing = useSignal(false);
  const hasInitialized = useSignal(false);

  // Initialisation du jeu
  const initializeGame = $(async () => {
    if (isInitializing.value || !isBrowser) return;
    
    try {
      isInitializing.value = true;
      error.value = null;
      
      console.log('Initialisation du jeu...');
      const response = await fetch(buildUrl(API_CONFIG.ROUTES.GAME.INITIALIZE), {
        method: 'POST',
        headers: {
          ...API_CONFIG.DEFAULT_HEADERS,
          'Origin': isBrowser ? window.location.origin : 'http://127.0.0.1:5173'
        },
        credentials: 'include',
        mode: 'cors'
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP! statut: ${response.status} - ${await response.text()}`);
      }
      
      const data = await response.json();
      console.log('Données reçues:', data);
      
      // Vérifier que l'état est complet
      if (!data?.state) {
        console.error('État du jeu invalide:', data);
        throw new Error('État du jeu invalide ou manquant');
      }

      // Mise à jour de l'état du jeu avec la propriété state
      gameState.value = data.state;
      console.log('État du jeu mis à jour:', gameState.value);
      
      if (!gameState.value?.narrative?.content) {
        throw new Error('Contenu narratif manquant dans l\'état du jeu');
      }
      
    } catch (e) {
      console.error('Erreur lors de l\'initialisation:', e);
      error.value = e instanceof Error ? e.message : 'Erreur inconnue lors de l\'initialisation du jeu';
      gameState.value = null;
    } finally {
      isInitializing.value = false;
      hasInitialized.value = true;
    }
  });

  // Gestion WebSocket - uniquement côté client
  useTask$(({ track, cleanup }) => {
    if (!isBrowser) return;

    // Suivre les changements d'état pour la connexion WebSocket
    track(() => hasInitialized.value);
    track(() => gameState.value);
    
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    
    const connect = () => {
      if (!hasInitialized.value || isConnected.value || !shouldReconnect.value || !gameState.value) return;
      
      try {
        console.log('Connexion WebSocket...');
        ws = new WebSocket(buildWsUrl());
        
        ws.onopen = () => {
          console.log('WebSocket connecté');
          isConnected.value = true;
          error.value = null;
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('Message WebSocket reçu:', data);
            
            // Vérifier que l'état est valide
            if (data.error) {
              error.value = data.error;
            } else if (data.state && typeof data.state === 'object') {
              const state = data.state;
              if (state.narrative?.content) {
                // Mettre à jour l'état du jeu
                gameState.value = {
                  game_id: state.game_id,
                  session_id: state.session_id,
                  narrative: state.narrative,
                  rules: state.rules || { needs_dice: false, dice_type: 'none' }
                };
                console.log('État WebSocket mis à jour:', gameState.value);
              } else {
                console.error('État WebSocket incomplet:', state);
              }
            }
          } catch (e) {
            console.error('Erreur parsing message WebSocket:', e);
          }
        };

        ws.onerror = (e) => {
          console.error('Erreur WebSocket:', e);
          error.value = 'Erreur de connexion WebSocket';
          isConnected.value = false;
        };

        ws.onclose = () => {
          console.log('WebSocket fermé');
          isConnected.value = false;
          ws = null;
          
          if (shouldReconnect.value && hasInitialized.value && gameState.value) {
            reconnectTimeout = setTimeout(connect, 1000);
          }
        };
        
      } catch (e) {
        console.error('Erreur setup WebSocket:', e);
        error.value = 'Erreur de connexion WebSocket';
        isConnected.value = false;
      }
    };

    // Nettoyage
    cleanup(() => {
      shouldReconnect.value = false;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    });

    // Connexion WebSocket si le jeu est initialisé
    if (hasInitialized.value && gameState.value) {
      connect();
    }
  });

  // Initialisation automatique - une seule fois au démarrage
  useTask$(({ track }) => {
    if (!isBrowser) return;
    
    // Initialiser uniquement si ce n'est pas déjà fait
    if (!hasInitialized.value && !isInitializing.value) {
      console.log('Démarrage de l\'initialisation...');
      initializeGame();
    }
  });

  return {
    gameState,
    error,
    isInitializing,
    isConnected,
    hasInitialized,
    initializeGame
  };
};
