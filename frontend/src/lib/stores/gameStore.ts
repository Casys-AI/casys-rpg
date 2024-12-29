import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type { GameState } from '$lib/types/game';

interface GameSession {
    sessionId: string | null;
    gameId: string | null;
}

interface Choice {
    id: string;
    text: string;
    metadata?: Record<string, any>;
}

interface GameChoices {
    available: Choice[];
    selected: Choice | null;
    history: Choice[];
}

interface NarrativeContent {
    sectionNumber: number;
    content: string;
    title?: string;
    metadata?: Record<string, any>;
}

interface GameNarrative {
    current: NarrativeContent | null;
    history: NarrativeContent[];
    lastUpdate: Date | null;
}

// Store pour la session (cookies)
function createGameSessionStore() {
    // Initialiser avec les valeurs des cookies si on est dans le navigateur
    const initialValue: GameSession = {
        sessionId: browser ? document.cookie.match(/session_id=([^;]+)/)?.[1] || null : null,
        gameId: browser ? document.cookie.match(/game_id=([^;]+)/)?.[1] || null : null
    };

    const { subscribe, set, update } = writable<GameSession>(initialValue);

    const store = {
        subscribe,
        setSession: (sessionId: string, gameId: string) => {
            // Mettre à jour les cookies
            if (browser) {
                document.cookie = `session_id=${sessionId}; path=/`;
                document.cookie = `game_id=${gameId}; path=/`;
            }
            // Mettre à jour le store
            set({ sessionId, gameId });
        },
        clearSession: () => {
            // Effacer les cookies
            if (browser) {
                document.cookie = 'session_id=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
                document.cookie = 'game_id=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT';
            }
            // Réinitialiser le store
            set({ sessionId: null, gameId: null });
        }
    };

    return store;
}

// Store pour l'état du jeu
function createGameStateStore() {
    const { subscribe, set, update } = writable<GameState | null>(null);

    return {
        subscribe,
        setState: (state: GameState) => {
            console.log('🎲 Updating game state:', state);
            set(state);
        },
        updateState: (partialState: Partial<GameState>) => {
            update(currentState => {
                if (!currentState) return partialState as GameState;
                return { ...currentState, ...partialState };
            });
        },
        reset: () => {
            console.log('🔄 Resetting game state');
            set(null);
        }
    };
}

// Store pour les choix du joueur
function createGameChoicesStore() {
    const initialState: GameChoices = {
        available: [],
        selected: null,
        history: []
    };

    const { subscribe, set, update } = writable<GameChoices>(initialState);

    return {
        subscribe,
        setAvailableChoices: (choices: Choice[]) => {
            console.log('🎯 Setting available choices:', choices);
            update(state => ({
                ...state,
                available: choices
            }));
        },
        selectChoice: (choice: Choice) => {
            console.log('✅ Selecting choice:', choice);
            update(state => ({
                ...state,
                selected: choice,
                history: [...state.history, choice]
            }));
        },
        clearChoices: () => {
            console.log('🔄 Clearing choices');
            update(state => ({
                ...state,
                available: [],
                selected: null
            }));
        },
        reset: () => {
            console.log('🔄 Resetting choices');
            set(initialState);
        }
    };
}

// Store pour la narration
function createGameNarrativeStore() {
    const initialState: GameNarrative = {
        current: null,
        history: [],
        lastUpdate: null
    };

    const { subscribe, set, update } = writable<GameNarrative>(initialState);

    return {
        subscribe,
        setNarrative: (content: NarrativeContent) => {
            console.log('📖 Setting narrative content:', content);
            update(state => {
                // Ajouter le contenu actuel à l'historique si il existe
                const newHistory = state.current 
                    ? [...state.history, state.current]
                    : state.history;
                
                return {
                    current: content,
                    history: newHistory,
                    lastUpdate: new Date()
                };
            });
        },
        updateMetadata: (metadata: Record<string, any>) => {
            update(state => {
                if (!state.current) return state;
                return {
                    ...state,
                    current: {
                        ...state.current,
                        metadata: {
                            ...state.current.metadata,
                            ...metadata
                        }
                    },
                    lastUpdate: new Date()
                };
            });
        },
        reset: () => {
            console.log('🔄 Resetting narrative');
            set(initialState);
        }
    };
}

// Créer les stores
const gameSession = createGameSessionStore();
const gameState = createGameStateStore();
const gameChoices = createGameChoicesStore();
const gameNarrative = createGameNarrativeStore();

// Store dérivé pour vérifier si une session est active
const hasActiveSession = derived(
    gameSession,
    $session => $session.sessionId !== null && $session.gameId !== null
);

// Store dérivé pour vérifier si des choix sont disponibles
const hasAvailableChoices = derived(
    gameChoices,
    $choices => $choices.available.length > 0
);

// Store dérivé pour le numéro de section actuel
const currentSectionNumber = derived(
    gameNarrative,
    $narrative => $narrative.current?.sectionNumber ?? 0
);

export { 
    gameSession, 
    gameState, 
    gameChoices,
    gameNarrative,
    hasActiveSession, 
    hasAvailableChoices,
    currentSectionNumber,
    type Choice,
    type GameChoices,
    type NarrativeContent,
    type GameNarrative
};
