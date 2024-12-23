import { component$ } from "@builder.io/qwik";
import type { DocumentHead } from "@builder.io/qwik-city";
import { NavBar } from "~/components/navigation/NavBar";
import { Link } from '@builder.io/qwik-city';

export default component$(() => {
  return (
    <div class="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900">
      <NavBar />
      <main class="flex-1 flex items-center justify-center">
        <div class="max-w-2xl mx-auto p-8 text-center">
          <h1 class="text-4xl font-bold mb-6 text-gray-800 dark:text-gray-100">
            Bienvenue dans Casys RPG
          </h1>
          <p class="text-xl mb-8 text-gray-600 dark:text-gray-300">
            Une aventure interactive où vos choix déterminent l'histoire
          </p>
          <Link 
            href="/game"
            class="inline-block px-8 py-4 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
          >
            Commencer l'aventure
          </Link>
          <p class="mt-4 text-sm text-gray-500 dark:text-gray-400">
            Accédez à l'espace auteur via la barre de navigation
          </p>
        </div>
      </main>
    </div>
  );
});

export const head: DocumentHead = {
  title: "Casys RPG - Accueil",
  meta: [
    {
      name: "description",
      content: "Une aventure interactive où vos choix déterminent l'histoire",
    },
  ],
};