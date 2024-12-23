import { component$, useVisibleTask$ } from "@builder.io/qwik";
import { useNavigate } from "@builder.io/qwik-city";
import type { DocumentHead } from "@builder.io/qwik-city";
import { GameBook } from "~/components/game/GameBook";
import { NavBar } from "~/components/navigation/NavBar";
import { API_CONFIG } from "~/config/api";

export default component$(() => {
  const nav = useNavigate();

  // Initialiser le jeu au chargement de la page
  // eslint-disable-next-line qwik/no-use-visible-task
  useVisibleTask$(async () => {
    try {
      console.log('🎮 Starting game initialization...');
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

  return (
    <div class="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900">
      <NavBar />
      <main class="flex-1">
        <GameBook />
      </main>
    </div>
  );
});

export const head: DocumentHead = {
  title: "Casys RPG - Livre-jeu interactif",
  meta: [
    {
      name: "description",
      content: "Une aventure interactive où vos choix déterminent l'histoire",
    },
  ],
};
