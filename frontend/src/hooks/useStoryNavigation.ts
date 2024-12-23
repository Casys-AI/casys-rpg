import { $, useSignal, type QRL } from '@builder.io/qwik';
import { API_CONFIG } from '~/config/api';

const API_BASE_URL = API_CONFIG.BASE_URL;

export const useStoryNavigation = () => {
  const navigating = useSignal(false);
  const error = useSignal<string | null>(null);

  const navigateToSection: QRL<(sectionNumber: string) => Promise<any>> = $(async (sectionNumber: string) => {
    if (navigating.value) return;
    navigating.value = true;
    error.value = null;

    try {
      console.log(`🔄 Navigating to section ${sectionNumber}...`);
      
      const actionRequest = {
        game_id: 'default', // On utilise 'default' comme ID par défaut
        action_type: 'navigate',
        data: {
          target_section: sectionNumber,
          user_response: `go_to_${sectionNumber}`,
          dice_result: null
        }
      };
      
      console.log('📤 Sending action request:', actionRequest);
      
      const actionResponse = await fetch(`${API_BASE_URL}/api/game/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(actionRequest),
      });

      console.log('📡 Action response status:', actionResponse.status);
      
      if (!actionResponse.ok) {
        const errorData = await actionResponse.json().catch(() => ({}));
        console.error('❌ Action response error:', errorData);
        throw new Error(errorData.detail || 'Failed to navigate to section');
      }

      const actionData = await actionResponse.json();
      console.log('📊 Action response data:', actionData);

      if (actionData.error) {
        throw new Error(actionData.error);
      }

      // Recharger l'état du jeu après la navigation
      console.log('🔄 Fetching updated game state...');
      const stateResponse = await fetch(`${API_BASE_URL}/api/game/state`);
      
      console.log('📡 State response status:', stateResponse.status);
      
      if (!stateResponse.ok) {
        const errorData = await stateResponse.json().catch(() => ({}));
        console.error('❌ State response error:', errorData);
        throw new Error(errorData.detail || 'Failed to get game state');
      }

      const stateData = await stateResponse.json();
      console.log('📊 State response data:', stateData);

      if (stateData.error) {
        throw new Error(stateData.error);
      }

      console.log('✅ Navigation successful');
      return stateData;

    } catch (error) {
      console.error('💥 Navigation error:', error);
      error.value = error instanceof Error ? error.message : 'Navigation failed';
      throw error;
    } finally {
      navigating.value = false;
    }
  });

  return {
    navigating,
    error,
    navigateToSection,
  };
};
