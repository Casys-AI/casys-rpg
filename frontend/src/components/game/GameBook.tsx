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
  const { gameState, error: wsError, isConnected, reconnect } = useGameState();
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
    if (wsError.value) {
      return (
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong class="font-bold">Erreur de connexion! </strong>
          <span class="block sm:inline">{wsError.value.message || wsError.value.toString()}</span>
          <button
            class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded ml-4 transition-colors"
            onClick$={reconnect}
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
        {!isConnected.value ? (
          <div class="flex items-center justify-center h-screen">
            <div class="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-gray-900">
              <span class="sr-only">Chargement...</span>
            </div>
          </div>
        ) : (
          <div class="container mx-auto">
            {renderError()}
            
            {navigationError.value && (
              <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative mb-8">
                {navigationError.value}
              </div>
            )}

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Zone principale de contenu */}
              <div class="lg:col-span-8">
                <div class="space-y-8">
                  {/* Debug logs */}
                  {console.log('Game state:', gameState.value)}
                  {console.log('Narrative:', gameState.value?.narrative)}
                  
                  <StoryContent
                    content={gameState.value?.narrative?.content || ''}
                    choices={gameState.value?.current_section?.choices || []}
                    onNavigate$={handleNavigate$}
                    loading={navigating.value}
                    actionMessage={actionMessage.value}
                  />
                  
                  <GameControls
                    gameState={gameState.value}
                    onAction$={handleNavigate$}
                  />
                  
                  <FeedbackPanel
                    gameState={gameState.value}
                    sectionNumber={gameState.value?.section_number || 1}
                  />
                </div>
              </div>

              {/* Panneau latéral */}
              <div class="lg:col-span-4 space-y-8">
                <CharacterSheet stats={gameState.value?.trace?.stats} />
                <DiceRoller />
              </div>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
});
