import { component$ } from "@builder.io/qwik";
import { StoryContent } from "~/components/story/StoryContent";
import { DiceRoller } from "~/components/dice/DiceRoller";
import { useGameState } from "~/hooks/useGameState";
import { useGameActions } from "~/hooks/useGameActions";

export const GameBook = component$(() => {
  const { gameState } = useGameState();
  const { handleNavigate$ } = useGameActions();

  if (!gameState.value) {
    return null;
  }

  const { narrative, rules } = gameState.value;

  return (
    <div class="min-h-screen bg-gray-50">
      <div class="container mx-auto">
        <StoryContent 
          content={narrative.content}
          choices={rules.choices || []}
          onNavigate$={handleNavigate$}
        />
        {rules?.needs_dice && (
          <div class="max-w-3xl mx-auto mt-8 bg-white p-6 rounded-lg shadow-sm">
            <DiceRoller 
              diceType={rules.dice_type}
            />
          </div>
        )}
      </div>
    </div>
  );
});
