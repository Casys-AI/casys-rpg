import { component$ } from "@builder.io/qwik";
import type { DocumentHead } from "@builder.io/qwik-city";
import { GameBook } from "~/components/game/GameBook";
import { NavBar } from "~/components/navigation/NavBar";

export default component$(() => {
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
