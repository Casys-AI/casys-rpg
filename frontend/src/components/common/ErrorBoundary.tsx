import { component$, Slot, useSignal, useOnDocument, $ } from '@builder.io/qwik';
import { API_CONFIG } from '~/config/api';

interface ErrorState {
  hasError: boolean;
  error?: Error;
  errorInfo?: string;
}

export const ErrorBoundary = component$(() => {
  const errorState = useSignal<ErrorState>({ hasError: false });

  // Utiliser useOnDocument pour le health check de manière non-bloquante
  useOnDocument('DOMContentLoaded', $(() => {
    const checkHealth = async () => {
      try {
        console.log('🏥 Checking API health...');
        
        // Vérifier l'état de l'API
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.HEALTH_CHECK_ENDPOINT}`);
        
        if (!response.ok) {
          console.error('❌ API health check failed:', response.statusText);
          throw new Error(`API inaccessible: ${response.statusText}`);
        }
        
        // Vérifier l'état de l'espace auteur
        const authorResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.HEALTH_CHECK_ENDPOINT}?check_type=author`);
        
        if (!authorResponse.ok) {
          console.error('❌ Author health check failed:', authorResponse.statusText);
          // Ne pas bloquer si l'espace auteur n'est pas accessible
          console.warn('⚠️ Author space not accessible, continuing anyway');
          return;
        }
        
        const authorHealth = await authorResponse.json();
        
        if (authorHealth.status !== 'ok') {
          console.warn('⚠️ Author space reported non-ok status:', authorHealth.message);
          // Ne pas bloquer si l'espace auteur n'est pas en état optimal
          return;
        }
        
        console.log('✅ Health checks successful');
        
      } catch (error) {
        console.error('💥 Health check error:', error);
        // Ne pas bloquer l'application si le health check échoue
        console.warn('⚠️ Health check failed, continuing anyway');
      }
    };
    
    checkHealth();
  }));

  if (errorState.value.hasError) {
    return (
      <div class="min-h-screen flex items-center justify-center bg-red-50">
        <div class="max-w-md p-8 bg-white rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold text-red-600 mb-4">
            Une erreur est survenue
          </h2>
          <p class="text-gray-600 mb-4">{errorState.value.errorInfo}</p>
          <p class="text-sm text-gray-500">
            {errorState.value.error?.message}
          </p>
          <button
            class="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            onClick$={() => window.location.reload()}
          >
            Rafraîchir la page
          </button>
        </div>
      </div>
    );
  }

  return <Slot />;
});
