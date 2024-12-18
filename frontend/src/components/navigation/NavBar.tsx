import { component$ } from '@builder.io/qwik';
import { Link } from '@builder.io/qwik-city';

export const NavBar = component$(() => {
  return (
    <nav class="bg-gray-800 text-white p-4">
      <div class="container mx-auto flex justify-between items-center">
        <div class="text-xl font-bold">Casys RPG</div>
        <div class="space-x-4">
          <Link href="/" class="hover:text-gray-300">
            Espace Lecteur
          </Link>
          <Link href="/author" class="hover:text-gray-300">
            Espace Auteur
          </Link>
        </div>
      </div>
    </nav>
  );
});
