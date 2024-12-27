import { component$, useVisibleTask$ } from "@builder.io/qwik";
import { useNavigate } from "@builder.io/qwik-city";
import type { DocumentHead } from "@builder.io/qwik-city";
import { NavBar } from "~/components/navigation/NavBar";
import { useGameState } from "~/hooks/useGameState";

export default component$(() => {
  const nav = useNavigate();
  const { gameState, error, initializeGame } = useGameState();

  // Initialiser le jeu au chargement de la page
  useVisibleTask$(async () => {
    try {
      // Si on n'a pas d'état, initialiser le jeu
      if (!gameState.value) {
        await initializeGame();
      }
      
      // Rediriger vers la page de lecture
      nav('/game/read');
      
    } catch (error) {
      console.error('💥 Game initialization error:', error);
      // Rediriger vers la page d'accueil en cas d'erreur
      nav('/');
    }
  });

  return (
    <div class="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900">
      <NavBar />
      <main class="flex-1 flex items-center justify-center">
        <div class="max-w-2xl mx-auto p-8 text-center">
          {error.value ? (
            <div class="text-red-500">
              {error.value}
            </div>
          ) : (
            <div class="text-gray-600 dark:text-gray-300">
              Chargement du jeu...
            </div>
          )}
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
