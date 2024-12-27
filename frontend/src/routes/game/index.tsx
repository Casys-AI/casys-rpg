import { component$, useTask$ } from "@builder.io/qwik";
import { useNavigate } from "@builder.io/qwik-city";
import type { DocumentHead } from "@builder.io/qwik-city";

export default component$(() => {
  const nav = useNavigate();

  // Rediriger automatiquement vers la page de lecture
  useTask$(() => {
    nav('/game/read');
  });
  
  return (
    <div class="flex items-center justify-center h-screen">
      <div class="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-gray-900">
        <span class="sr-only">Redirection...</span>
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: "Casys RPG",
  meta: [
    {
      name: "description",
      content: "Plongez dans l'aventure avec Casys RPG",
    },
  ],
};
