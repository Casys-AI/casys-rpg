import { component$ } from "@builder.io/qwik";
import type { DocumentHead } from "@builder.io/qwik-city";
import { GameBook } from "~/components/game/GameBook";
import { NavBar } from "~/components/navigation/NavBar";
import { useGameState } from "~/hooks/useGameState";
import { useNavigate } from "@builder.io/qwik-city";

export default component$(() => {
  const nav = useNavigate();
  const { gameState, error, isInitializing } = useGameState();

  // Si on a une erreur, afficher le message d'erreur
  if (error?.value) {
    console.error('Erreur détectée:', error.value);
    return (
      <div class="container mx-auto p-4">
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong class="font-bold">Erreur de chargement : </strong>
          <span class="block sm:inline">{error.value}</span>
          <div class="mt-4">
            <pre class="text-sm bg-red-50 p-2 rounded overflow-auto max-h-96">
              {JSON.stringify(gameState.value, null, 2)}
            </pre>
          </div>
          <button
            class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded mt-4"
            onClick$={() => nav('/')}
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  // Si on est en train d'initialiser, afficher le loader
  if (isInitializing.value) {
    return (
      <div class="flex items-center justify-center h-screen">
        <div class="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-gray-900">
          <span class="sr-only">Chargement...</span>
        </div>
      </div>
    );
  }

  // Si on n'a pas d'état de jeu, afficher le message
  if (!gameState.value) {
    return (
      <div class="flex items-center justify-center h-screen">
        <div class="text-center">
          <h2 class="text-xl font-bold mb-4">Aucune partie en cours</h2>
          <p class="text-gray-600 mb-4">Veuillez commencer une nouvelle partie depuis l'accueil.</p>
          <button
            onClick$={() => nav('/')}
            class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  // Si tout est ok, afficher le jeu
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
  title: "Casys RPG - Lecture",
  meta: [
    {
      name: "description",
      content: "Lisez votre aventure et faites vos choix",
    },
  ],
};
