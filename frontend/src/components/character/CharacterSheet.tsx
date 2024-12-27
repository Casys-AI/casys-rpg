import { component$ } from '@builder.io/qwik';
import type { CharacterStats } from '~/types/game';

interface CharacterSheetProps {
  stats: CharacterStats;
}

export const CharacterSheet = component$<CharacterSheetProps>(({ stats }) => {
  if (!stats || !stats.Caractéristiques) {
    return <div class="text-red-500">Chargement des statistiques...</div>;
  }

  return (
    <div class="bg-white p-6 rounded-lg shadow-lg">
      {/* Caractéristiques */}
      <div class="mb-6">
        <h3 class="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Caractéristiques</h3>
        <div class="grid grid-cols-1 gap-3">
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Habileté</span>
            <span class="font-medium">{stats.Caractéristiques.Habileté}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Endurance</span>
            <span class="font-medium">{stats.Caractéristiques.Endurance}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Chance</span>
            <span class="font-medium">{stats.Caractéristiques.Chance}</span>
          </div>
        </div>
      </div>

      {/* Ressources */}
      <div class="mb-6">
        <h3 class="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Ressources</h3>
        <div class="grid grid-cols-1 gap-3">
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Or</span>
            <span class="font-medium">{stats.Ressources.Or}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Gemmes</span>
            <span class="font-medium">{stats.Ressources.Gemme}</span>
          </div>
        </div>
      </div>

      {/* Inventaire */}
      <div>
        <h3 class="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Inventaire</h3>
        {stats.Inventaire.Objets.length > 0 ? (
          <ul class="list-disc list-inside space-y-2">
            {stats.Inventaire.Objets.map((item, index) => (
              <li key={index} class="text-gray-600">{item}</li>
            ))}
          </ul>
        ) : (
          <p class="text-gray-500 italic">Inventaire vide</p>
        )}
      </div>
    </div>
  );
});
