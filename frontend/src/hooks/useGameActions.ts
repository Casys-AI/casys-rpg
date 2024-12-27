import { $, useSignal } from '@builder.io/qwik';
import { API_CONFIG, buildUrl } from '~/config/api';

export function useGameActions() {
  const isLoading = useSignal(false);
  const error = useSignal<string | null>(null);

  // Envoyer une action
  const sendAction = $(async (action: string) => {
    try {
      isLoading.value = true;
      const response = await fetch(buildUrl(API_CONFIG.ROUTES.GAME.ACTION), {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS,
        body: JSON.stringify({ action })
      });

      if (!response.ok) {
        throw new Error('Failed to send action');
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      isLoading.value = false;
    }
  });

  // Naviguer vers une section
  const navigateToSection = $(async (section: number) => {
    try {
      isLoading.value = true;
      const response = await fetch(buildUrl(API_CONFIG.ROUTES.GAME.NAVIGATE(section)), {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS
      });

      if (!response.ok) {
        throw new Error('Failed to navigate');
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      isLoading.value = false;
    }
  });

  // Soumettre une réponse
  const submitResponse = $(async (response: string) => {
    try {
      isLoading.value = true;
      const resp = await fetch(buildUrl(API_CONFIG.ROUTES.GAME.RESPONSE), {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS,
        body: JSON.stringify({ response })
      });

      if (!resp.ok) {
        throw new Error('Failed to submit response');
      }

      return await resp.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      isLoading.value = false;
    }
  });

  // Arrêter le jeu
  const stopGame = $(async () => {
    try {
      isLoading.value = true;
      const response = await fetch(buildUrl(API_CONFIG.ROUTES.GAME.STOP), {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS
      });

      if (!response.ok) {
        throw new Error('Failed to stop game');
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      isLoading.value = false;
    }
  });

  // Lancer un dé
  const rollDice = $(async (diceType: string) => {
    try {
      isLoading.value = true;
      const response = await fetch(buildUrl(API_CONFIG.ROUTES.UTILS.ROLL_DICE(diceType)), {
        method: 'GET',
        headers: API_CONFIG.DEFAULT_HEADERS
      });

      if (!response.ok) {
        throw new Error('Failed to roll dice');
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      isLoading.value = false;
    }
  });

  return {
    isLoading,
    error,
    sendAction,
    navigateToSection,
    submitResponse,
    stopGame,
    rollDice
  };
}
