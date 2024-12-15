import { component$ } from '@builder.io/qwik';
import { useStore } from '@builder.io/qwik';

interface GameContentProps {
  content: string;
  choices: Array<{
    id: number;
    text: string;
  }>;
  onChoice$: (choiceId: number) => void;
  showDiceRoll: boolean;
  onRollDice$: () => void;
}

export const GameContent = component$<GameContentProps>(({
  content,
  choices,
  onChoice$,
  showDiceRoll,
  onRollDice$
}) => {
  const state = useStore({
    selectedChoice: -1
  });

  return (
    <div class="bg-white shadow-lg rounded-lg p-6">
      {/* Game Text */}
      <div 
        class="prose prose-lg max-w-none mb-8"
        dangerouslySetInnerHTML={content}
      />

      {/* Dice Roll Button */}
      {showDiceRoll && (
        <div class="mb-8">
          <button
            onClick$={onRollDice$}
            class="w-full bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 transition flex items-center justify-center space-x-2"
          >
            <span class="text-2xl">🎲</span>
            <span>Lancer les dés</span>
          </button>
        </div>
      )}

      {/* Choices */}
      {choices.length > 0 && (
        <div class="space-y-4">
          <h3 class="text-xl font-bold">Que souhaitez-vous faire ?</h3>
          <div class="space-y-3">
            {choices.map((choice) => (
              <button
                key={choice.id}
                onClick$={() => {
                  state.selectedChoice = choice.id;
                  onChoice$(choice.id);
                }}
                class={`w-full text-left p-4 rounded-lg border-2 transition
                  ${state.selectedChoice === choice.id
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                  }`}
              >
                {choice.text}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});
