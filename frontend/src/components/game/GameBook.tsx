import { component$, useSignal, useTask$, useStore, useStyles$, $ } from '@builder.io/qwik';
import { GameState } from '~/types/game';
import { CharacterSheet } from '../character/CharacterSheet';
import { StoryContent } from '../story/StoryContent';
import { GameControls } from '../controls/GameControls';
import { FeedbackPanel } from '../feedback/FeedbackPanel';
import { DiceRoller } from '../dice/DiceRoller';
import { useStoryNavigation } from '~/hooks/useStoryNavigation';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const GameBook = component$(() => {
  const gameState = useStore<GameState>({
    section_number: 1,
    current_section: {
      number: 1,
      content: '',
      choices: []
    },
    needs_content: true,
    trace: {
      stats: {
        Caractéristiques: {
          Habileté: 10,
          Endurance: 20,
          Chance: 8
        },
        Ressources: {
          Or: 100,
          Gemme: 5
        },
        Inventaire: {
          Objets: ['Épée', 'Bouclier']
        }
      },
      history: []
    },
    action_message: ''
  });

  const loading = useSignal(true);
  const error = useSignal<string | null>(null);
  const mounted = useSignal(false);

  const { navigating, navigateToSection, error: navigationError } = useStoryNavigation();

  const handleNavigate$ = $(async (sectionNumber: string) => {
    try {
      const result = await navigateToSection(sectionNumber);
      if (result?.state) {
        Object.assign(gameState, result.state);
        // Si nous avons un message d'action, l'afficher via la boîte de dialogue
        if (result.state.action_message) {
          showDialog(result.state.action_message);
        }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Une erreur est survenue';
    }
  });

  const handleAction$ = $(async (action: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/game/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_response: action }),
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'envoi de l\'action');
      }

      const result = await response.json();
      if (result?.state) {
        Object.assign(gameState, result.state);
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Une erreur est survenue';
    }
  });

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

  // Charger l'état initial du jeu
  useTask$(async () => {
    if (!mounted.value) {
      mounted.value = true;
      loading.value = true;
      try {
        console.log('Fetching initial game state...');
        const response = await fetch(`${API_BASE_URL}/game/state`);
        console.log('Initial state response status:', response.status);
        
        if (!response.ok) {
          throw new Error('Failed to fetch initial game state');
        }

        const data = await response.json();
        console.log('Initial state data:', data);
        
        if (data.state) {
          Object.assign(gameState, data.state);
        }
      } catch (e) {
        console.error('Error fetching initial state:', e);
        error.value = e instanceof Error ? e.message : 'Failed to initialize game';
      } finally {
        loading.value = false;
      }
    }
  });

  return (
    <div class="game-book">
      <div class="game-layout">
        <div class="character-panel">
          <CharacterSheet stats={gameState.trace.stats} />
        </div>
        <div class="story-panel">
          {loading.value ? (
            <div class="loading">
              <div class="loading-spinner" />
              <div class="loading-text">Chargement...</div>
            </div>
          ) : error.value ? (
            <div class="error">{error.value}</div>
          ) : (
            <>
              <StoryContent
                content={gameState.current_section.content}
                choices={gameState.current_section.choices}
                onNavigate$={handleNavigate$}
                actionMessage={gameState.action_message}
                onAction$={handleAction$}
              />
              <GameControls gameState={gameState} />
            </>
          )}
        </div>
        <div class="feedback-panel">
          <FeedbackPanel />
        </div>
      </div>
    </div>
  );
});
