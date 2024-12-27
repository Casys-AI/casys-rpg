import { $, useSignal } from '@builder.io/qwik';
import { API_CONFIG, buildUrl } from '~/config/api';

export interface GameFeedback {
  feedback_id: string;
  user_id: string;
  content: string;
  timestamp: string;
}

export function useGameFeedback() {
  const isLoading = useSignal(false);
  const error = useSignal<string | null>(null);

  // Envoyer un feedback
  const sendFeedback = $(async (content: string) => {
    try {
      isLoading.value = true;
      const response = await fetch(buildUrl(API_CONFIG.ROUTES.UTILS.FEEDBACK), {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS,
        body: JSON.stringify({ content })
      });

      if (!response.ok) {
        throw new Error('Failed to send feedback');
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      isLoading.value = false;
    }
  });

  // Obtenir le feedback sur l'état actuel
  const getGameFeedback = $(async () => {
    try {
      isLoading.value = true;
      const response = await fetch(buildUrl(API_CONFIG.ROUTES.GAME.FEEDBACK), {
        method: 'GET',
        headers: API_CONFIG.DEFAULT_HEADERS
      });

      if (!response.ok) {
        throw new Error('Failed to get game feedback');
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
    sendFeedback,
    getGameFeedback
  };
}
