import { component$, useSignal, useTask$, type QRL } from '@builder.io/qwik';
import type { GameState } from '../../types/game';
import { DiceRoller } from '../dice/DiceRoller';

interface GameBookProps {
  gameState: GameState;
  onNavigate$?: QRL<(target: string) => Promise<void>>;
}

export const GameBook = component$<GameBookProps>(({ gameState, onNavigate$ }) => {
  const contentRef = useSignal<HTMLDivElement>();
  const showDice = useSignal(gameState.rules?.needs_dice || false);

  // Mettre à jour l'affichage des dés quand l'état change
  useTask$(({ track }) => {
    const state = track(() => gameState);
    showDice.value = state.rules?.needs_dice || false;
  });

  return (
    <div class="min-h-screen bg-white">
      <div class="w-full px-1 sm:px-2">
        {/* Contenu principal */}
        <div ref={contentRef} class="w-full max-w-5xl mx-auto">
          <h1 class="text-4xl font-bold text-center mb-8">
            Section {gameState.narrative.section_number}
          </h1>
          
          <div class="prose prose-lg mx-auto text-justify w-full max-w-none">
            {gameState.narrative.content.split('\n').map((line, index) => (
              <p key={index} class="mb-6">{line}</p>
            ))}
          </div>

          {/* Choix */}
          {gameState.choices && gameState.choices.length > 0 && (
            <div class="mt-12 space-y-6">
              <h2 class="text-2xl font-bold text-center text-black">
                Que souhaitez-vous faire ?
              </h2>
              <div class="space-y-4">
                {gameState.choices.map((choice, index) => (
                  <button
                    key={index}
                    onClick$={() => onNavigate$?.(choice.target)}
                    class="w-full text-left p-4 rounded-lg border border-gray-200
                           hover:bg-gray-50 transition-colors duration-200"
                  >
                    {choice.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Dés */}
          {showDice.value && (
            <div class="mt-12">
              <DiceRoller type={gameState.rules.dice_type} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
