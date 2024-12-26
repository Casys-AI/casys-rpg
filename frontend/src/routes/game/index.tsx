import { component$, useVisibleTask$ } from "@builder.io/qwik";
import { useNavigate } from "@builder.io/qwik-city";
import type { DocumentHead } from "@builder.io/qwik-city";
import { NavBar } from "~/components/navigation/NavBar";
import { API_CONFIG, updateApiConfig } from "~/config/api";

export default component$(() => {
  const nav = useNavigate();

  // Initialiser le jeu au chargement de la page
  // eslint-disable-next-line qwik/no-use-visible-task
  useVisibleTask$(async () => {
    try {
      console.log('🎮 Starting game initialization...');
      
      // Mettre à jour la configuration avec le bon port
      await updateApiConfig();
      
      const initUrl = `${API_CONFIG.BASE_URL}/api/game/initialize`;
      console.log(`🔍 Init URL: ${initUrl}`);
      
      const response = await fetch(initUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('📡 Init response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Game initialization failed:', errorText);
        throw new Error(`Failed to initialize game: ${response.statusText}`);
      }
      
      try {
        const data = await response.json();
        console.log('📊 Init data:', data);
        console.log('✅ Game initialized successfully');
        
        // Rediriger vers la page de lecture après l'initialisation réussie
        nav('/game/read');
        
      } catch (parseError) {
        console.error('❌ Failed to parse response:', parseError);
        throw new Error('Invalid server response');
      }
      
    } catch (error) {
      console.error('💥 Game initialization error:', error);
      // Rediriger vers la page d'accueil en cas d'erreur
      nav('/');
    }
  });

  // Afficher un écran de chargement pendant l'initialisation
  return (
    <div class="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900">
      <NavBar />
      <main class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <h2 class="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200">
            Initialisation du jeu...
          </h2>
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
        </div>
      </main>
    </div>
  );
});

export const head: DocumentHead = {
  title: "Casys RPG - Initialisation",
  meta: [
    {
      name: "description",
      content: "Initialisation de votre aventure",
    },
  ],
};
