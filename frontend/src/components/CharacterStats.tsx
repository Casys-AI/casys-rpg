import { component$ } from '@builder.io/qwik';

interface CharacterStatsProps {
  stats: {
    strength: number;
    dexterity: number;
    intelligence: number;
    health: number;
    maxHealth: number;
    experience: number;
    level: number;
  };
}

export const CharacterStats = component$<CharacterStatsProps>(({ stats }) => {
  const healthPercentage = (stats.health / stats.maxHealth) * 100;
  
  return (
    <div class="bg-white shadow-lg rounded-lg p-4">
      <h2 class="text-xl font-bold mb-4">📊 Statistiques</h2>
      
      {/* Health Bar */}
      <div class="mb-4">
        <div class="flex justify-between text-sm mb-1">
          <span>Santé</span>
          <span>{stats.health}/{stats.maxHealth}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2.5">
          <div
            class="bg-green-600 h-2.5 rounded-full transition-all"
            style={{ width: `${healthPercentage}%` }}
          />
        </div>
      </div>

      {/* Main Stats */}
      <div class="space-y-2">
        <div class="flex justify-between">
          <span>Force</span>
          <span class="font-medium">{stats.strength}</span>
        </div>
        <div class="flex justify-between">
          <span>Dextérité</span>
          <span class="font-medium">{stats.dexterity}</span>
        </div>
        <div class="flex justify-between">
          <span>Intelligence</span>
          <span class="font-medium">{stats.intelligence}</span>
        </div>
      </div>

      {/* Level and XP */}
      <div class="mt-4 pt-4 border-t">
        <div class="flex justify-between">
          <span>Niveau</span>
          <span class="font-medium">{stats.level}</span>
        </div>
        <div class="flex justify-between">
          <span>Expérience</span>
          <span class="font-medium">{stats.experience}</span>
        </div>
      </div>
    </div>
  );
});
