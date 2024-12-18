import { component$, Slot, useSignal, useVisibleTask$ } from '@builder.io/qwik';

interface ErrorState {
  hasError: boolean;
  error?: Error;
  errorInfo?: string;
}

export const ErrorBoundary = component$(() => {
  const errorState = useSignal<ErrorState>({ hasError: false });

  useVisibleTask$(async () => {
    try {
      // Vérifier l'état de l'API
      const response = await fetch('http://localhost:8000/api/health');
      if (!response.ok) {
        throw new Error(`API inaccessible: ${response.statusText}`);
      }
      
      // Vérifier l'état de l'espace auteur
      const authorResponse = await fetch('http://localhost:8000/api/author/health');
      if (!authorResponse.ok) {
        throw new Error(`Espace auteur inaccessible: ${authorResponse.statusText}`);
      }
      
      const authorHealth = await authorResponse.json();
      if (authorHealth.status !== 'ok') {
        throw new Error(authorHealth.message);
      }
    } catch (error) {
      errorState.value = {
        hasError: true,
        error: error as Error,
        errorInfo: 'Erreur de connexion à l\'API'
      };
    }
  });

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
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return <Slot />;
});
