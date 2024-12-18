import { component$, useSignal, $, useStyles$ } from '@builder.io/qwik';
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
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong class="font-bold">Erreur de connexion!</strong>
          <span class="block sm:inline"> {wsError}</span>
          <button
            class="bg-red-500 text-white px-4 py-2 rounded ml-4"
            onClick$={reconnect}
          >
            Reconnecter
          </button>
        </div>
      );
    }
    return null;
  };

  useStyles$(`
    .game-book {
      min-height: 100vh;
      padding: var(--spacing-lg);
      background: var(--color-paper);
    }

    .game-layout {
      display: grid;
      grid-template-columns: 300px 1fr 300px;
      gap: var(--spacing-xl);
      max-width: 1600px;
      margin: 0 auto;
    }

    .character-panel, .story-panel, .feedback-panel {
      padding: var(--spacing-lg);
    }

    .loading {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 300px;
    }

    .loading-spinner {
      width: 50px;
      height: 50px;
      border: 5px solid var(--shadow-light);
      border-top-color: var(--color-ink);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    .loading-text {
      margin-top: var(--spacing-md);
      color: var(--color-ink-light);
      font-family: var(--font-secondary);
    }

    .error {
      padding: var(--spacing-lg);
      text-align: center;
      color: var(--color-ink);
    }

    .error p {
      margin-bottom: var(--spacing-md);
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }

    @media (max-width: 1200px) {
      .game-layout {
        grid-template-columns: 250px 1fr 250px;
      }
    }

    @media (max-width: 1024px) {
      .game-layout {
        grid-template-columns: 1fr;
        gap: var(--spacing-lg);
      }
    }

    @media (max-width: 768px) {
      .game-book {
        padding: var(--spacing-md);
      }
    }
  `);

  return (
    <ErrorBoundary>
      <div class="game-book">
        {!isConnected.value ? (
          <div class="flex items-center justify-center h-screen">
            <div class="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-gray-900"></div>
          </div>
        ) : (
          <div class="container mx-auto px-4 py-8">
            {renderError()}
            {navigationError.value && (
              <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative">
                {navigationError.value}
              </div>
            )}
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div class="md:col-span-2">
                <StoryContent
                  content={gameState.value?.current_section.content || ''}
                  choices={gameState.value?.current_section.choices || []}
                  onNavigate$={handleNavigate$}
                  loading={navigating.value}
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
              <div>
                <CharacterSheet stats={gameState.value?.trace.stats} />
                <DiceRoller />
              </div>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
});
