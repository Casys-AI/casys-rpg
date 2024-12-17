import { component$ } from "@builder.io/qwik";
import type { DocumentHead } from "@builder.io/qwik-city";
import { GameBook } from "~/components/game/GameBook";

export default component$(() => {
  return (
    <div class="min-h-screen bg-gray-100 dark:bg-gray-900">
      <GameBook />
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