import { component$, useContext } from '@builder.io/qwik';
import { GameContext } from '~/routes/store';

export default component$(() => {
  const store = useContext(GameContext);
  const stats = store.gameState.trace.stats;

  return (
    <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
      <h2 class="text-xl font-bold mb-4 text-white">Statistiques du Personnage</h2>
      
      {/* Caractéristiques */}
      <div class="mb-4">
        <h3 class="text-lg font-semibold mb-2 text-gray-300">Caractéristiques</h3>
        <div class="grid grid-cols-2 gap-2">
          <div class="text-gray-400">Habileté</div>
          <div class="text-white">{stats.Caractéristiques.Habileté}</div>
          <div class="text-gray-400">Endurance</div>
          <div class="text-white">{stats.Caractéristiques.Endurance}</div>
          <div class="text-gray-400">Chance</div>
          <div class="text-white">{stats.Caractéristiques.Chance}</div>
        </div>
      </div>
      
      {/* Ressources */}
      <div class="mb-4">
        <h3 class="text-lg font-semibold mb-2 text-gray-300">Ressources</h3>
        <div class="grid grid-cols-2 gap-2">
          <div class="text-gray-400">Or</div>
          <div class="text-white">{stats.Ressources.Or}</div>
          <div class="text-gray-400">Gemmes</div>
          <div class="text-white">{stats.Ressources.Gemme}</div>
        </div>
      </div>
      
      {/* Inventaire */}
      <div>
        <h3 class="text-lg font-semibold mb-2 text-gray-300">Inventaire</h3>
        <ul class="list-disc list-inside text-white">
          {stats.Inventaire.Objets.map((item, index) => (
            <li key={index} class="text-gray-300">{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
});
