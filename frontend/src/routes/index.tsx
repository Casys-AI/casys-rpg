import { component$ } from '@builder.io/qwik';
import { type DocumentHead, Link } from '@builder.io/qwik-city';

export default component$(() => {
  return (
    <div class="min-h-screen flex items-center justify-center bg-gray-900 text-white">
      <div class="text-center">
        <h1 class="text-4xl font-bold mb-8">Bienvenue dans Casys RPG</h1>
        <p class="mb-8">Une aventure interactive passionnante vous attend...</p>
        <Link 
          href="/game" 
          class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg 
                 hover:bg-blue-700 transition-colors"
        >
          Accéder au jeu
        </Link>
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: 'Casys RPG',
  meta: [
    {
      name: 'description',
      content: 'Casys RPG - Une aventure interactive'
    }
  ]
};