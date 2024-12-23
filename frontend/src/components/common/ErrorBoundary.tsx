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
        console.log(`🔍 Health check URL: ${API_CONFIG.BASE_URL}${API_CONFIG.HEALTH_CHECK_ENDPOINT}`);
        
        // Vérifier l'état de l'API
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.HEALTH_CHECK_ENDPOINT}`);
        console.log('📡 Health check response:', response);
        
        if (!response.ok) {
          console.error('❌ API health check failed:', response.statusText);
          throw new Error(`API inaccessible: ${response.statusText}`);
        }
        
        console.log('✅ API health check successful');
        
        // Vérifier l'état de l'espace auteur
        console.log('🏥 Checking author space...');
        const authorResponse = await fetch(`${API_CONFIG.BASE_URL}/api/author/health`);
        console.log('📡 Author health check response:', authorResponse);
        
        if (!authorResponse.ok) {
          console.error('❌ Author health check failed:', authorResponse.statusText);
          throw new Error(`Espace auteur inaccessible: ${authorResponse.statusText}`);
        }
        
        const authorHealth = await authorResponse.json();
        console.log('📊 Author health data:', authorHealth);
        
        if (authorHealth.status !== 'ok') {
          console.error('❌ Author space reported error:', authorHealth.message);
          throw new Error(authorHealth.message);
        }
        
        console.log('✅ Author health check successful');
      } catch (error) {
        console.error('💥 Health check error:', error);
        errorState.value = {
          hasError: true,
          error: error as Error,
          errorInfo: 'Erreur de connexion à l\'API'
        };
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
