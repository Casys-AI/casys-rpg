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
        const healthEndpoint = '/api/health';
        const response = await fetch(`${API_CONFIG.BASE_URL}${healthEndpoint}`);
        
        if (!response.ok) {
          console.error('❌ API health check failed:', response.statusText);
          throw new Error(`API inaccessible: ${response.statusText}`);
        }
        
        console.log('✅ Health check successful');
        
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
      <div class="min-h-screen flex items-center justify-center bg-gray-100">
        <div class="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <h2 class="text-2xl font-bold text-red-600 mb-4">Une erreur est survenue</h2>
          <p class="text-gray-600 mb-4">
            {errorState.value.error?.message || "Une erreur inattendue s'est produite."}
          </p>
          <pre class="bg-gray-100 p-4 rounded text-sm overflow-auto">
            {errorState.value.errorInfo}
          </pre>
          <button
            class="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick$={() => window.location.reload()}
          >
            Recharger la page
          </button>
        </div>
      </div>
    );
  }

  return <Slot />;
});
