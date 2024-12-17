import { component$, useContext } from '@builder.io/qwik';
import { GameStateContext } from '../routes/store';

export const CharacterSheet = component$(() => {
  const gameState = useContext(GameStateContext);

  const stats = gameState.character;

  const getModifier = (value: number) => {
    return Math.floor((value - 10) / 2);
  };

  return (
    <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 class="text-2xl font-bold mb-6">Character Sheet</h2>
      
      {/* Health Bar */}
      <div class="mb-6">
        <div class="flex justify-between mb-2">
          <span>Health</span>
          <span>{stats.health} / {stats.maxHealth}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
          <div
            class="bg-red-600 h-2.5 rounded-full"
            style={{ width: `${(stats.health / stats.maxHealth) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Stats Grid */}
      <div class="grid grid-cols-2 gap-4">
        {Object.entries(stats)
          .filter(([key]) => !['health', 'maxHealth', 'experience'].includes(key))
          .map(([key, value]) => (
            <div key={key} class="bg-gray-50 dark:bg-gray-700 p-3 rounded">
              <div class="text-sm text-gray-600 dark:text-gray-400 capitalize">
                {key}
              </div>
              <div class="flex justify-between items-baseline">
                <span class="text-xl font-bold">{value}</span>
                <span class="text-sm text-gray-500">
                  {getModifier(value) >= 0 ? '+' : ''}{getModifier(value)}
                </span>
              </div>
            </div>
          ))}
      </div>

      {/* Experience */}
      <div class="mt-6">
        <div class="flex justify-between text-sm text-gray-600 dark:text-gray-400">
          <span>Experience</span>
          <span>{stats.experience}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-1.5 dark:bg-gray-700 mt-1">
          <div
            class="bg-blue-600 h-1.5 rounded-full"
            style={{ width: `${(stats.experience % 1000) / 10}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
});
