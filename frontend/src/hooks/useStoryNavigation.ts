import { $, useSignal, type QRL } from '@builder.io/qwik';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const useStoryNavigation = () => {
  const navigating = useSignal(false);
  const error = useSignal<string | null>(null);

  const navigateToSection: QRL<(sectionNumber: string) => Promise<any>> = $(async (sectionNumber: string) => {
    if (navigating.value) return;
    navigating.value = true;
    error.value = null;

    try {
      console.log(`Navigating to section ${sectionNumber}...`);
      
      const actionResponse = await fetch(`${API_BASE_URL}/game/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_response: `go_to_${sectionNumber}`,
          dice_result: null
        }),
      });

      console.log('Action response status:', actionResponse.status);
      
      if (!actionResponse.ok) {
        const errorData = await actionResponse.json().catch(() => ({}));
        console.error('Action response error:', errorData);
        throw new Error(errorData.detail || 'Failed to navigate to section');
      }

      const actionData = await actionResponse.json();
      console.log('Action response data:', actionData);

      if (actionData.error) {
        throw new Error(actionData.error);
      }

      // Recharger l'état du jeu après la navigation
      console.log('Fetching updated game state...');
      const stateResponse = await fetch(`${API_BASE_URL}/game/state`);
      
      console.log('State response status:', stateResponse.status);
      
      if (!stateResponse.ok) {
        const errorData = await stateResponse.json().catch(() => ({}));
        console.error('State response error:', errorData);
        throw new Error(errorData.detail || 'Failed to fetch game state');
      }

      const stateData = await stateResponse.json();
      console.log('State response data:', stateData);
      console.log('Content type:', typeof stateData.state.current_section.content);
      console.log('Content value:', stateData.state.current_section.content);

      if (stateData.error) {
        throw new Error(stateData.error);
      }

      // Si le contenu est un objet, on extrait la propriété html
      const content = stateData.state.current_section.content;
      const processedContent = typeof content === 'object' && content.html 
        ? content.html 
        : content.toString();

      return {
        state: {
          ...stateData.state,
          current_section: {
            ...stateData.state.current_section,
            content: processedContent
          }
        }
      };
    } catch (e) {
      console.error('Navigation error:', e);
      error.value = e instanceof Error ? e.message : 'Une erreur est survenue';
      throw e;
    } finally {
      navigating.value = false;
    }
  });

  return {
    navigating,
    navigateToSection,
    error
  };
};
