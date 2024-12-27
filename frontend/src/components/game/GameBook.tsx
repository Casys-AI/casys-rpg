import { component$, useSignal, $ } from '@builder.io/qwik';
import { CharacterSheet } from '../character/CharacterSheet';
import { StoryContent } from '../story/StoryContent';
import { GameControls } from '../controls/GameControls';
import { FeedbackPanel } from '../feedback/FeedbackPanel';
import { DiceRoller } from '../dice/DiceRoller';
import { useStoryNavigation } from '~/hooks/useStoryNavigation';
import { useGameState } from '~/hooks/useGameState';
import { ErrorBoundary } from '../common/ErrorBoundary';

export const GameBook = component$(() => {
  const { gameState, error: wsError, initializeGame } = useGameState();
  const loading = useSignal(true);
  const { navigating, navigateToSection, error: navigationError } = useStoryNavigation();
  const actionMessage = useSignal('');

  const handleNavigate$ = $(async (sectionNumber: string) => {
    try {
      await navigateToSection(sectionNumber);
    } catch (err) {
      console.error('Navigation error:', err);
    }
  });

  // Afficher un message d'erreur si la connexion WebSocket est perdue
  const renderError = () => {
    if (wsError) {
      return (
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong class="font-bold">Erreur de connexion! </strong>
          <span class="block sm:inline">{wsError}</span>
          <button
            class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded ml-4 transition-colors"
            onClick$={initializeGame}
          >
            Reconnecter
          </button>
        </div>
      );
    }
    return null;
  };

  return (
    <ErrorBoundary>
      <div class="min-h-screen p-4 md:p-8 bg-paper">
        {!gameState.value ? (
          <div class="flex items-center justify-center h-screen">
            <div class="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-gray-900">
              <span class="sr-only">Chargement...</span>
            </div>
          </div>
        ) : (
          <div class="container mx-auto">
            {renderError()}
            <div class="grid grid-cols-1 md:grid-cols-12 gap-4">
              {/* Panneau latéral gauche */}
              <div class="md:col-span-3">
                <CharacterSheet character={gameState.value.character} />
              </div>

              {/* Contenu principal */}
              <div class="md:col-span-6">
                <StoryContent 
                  content={gameState.value.content}
                  loading={loading.value}
                  error={navigationError.value}
                />
                <GameControls
                  onNavigate$={handleNavigate$}
                  loading={navigating.value}
                  options={gameState.value.options || []}
                />
              </div>

              {/* Panneau latéral droit */}
              <div class="md:col-span-3">
                <DiceRoller />
                <FeedbackPanel message={actionMessage.value} />
              </div>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
});
