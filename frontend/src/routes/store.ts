import { createContextId } from '@builder.io/qwik';

export interface GameState {
  sectionNumber: number;
  content: string | null;
  rules: any;
  decision: any;
  trace: {
    stats: {
      Caractéristiques: {
        Habileté: number;
        Endurance: number;
        Chance: number;
      };
      Ressources: {
        Or: number;
        Gemme: number;
      };
      Inventaire: {
        Objets: string[];
      };
    };
  };
  error: string | null;
}

export interface GameStore {
  gameState: GameState;
  userResponse: string;
  diceResult: number | null;
  feedbackMode: boolean;
  previousSection: any;
}

export const GameContext = createContextId<GameStore>('game-store');

export const initialGameState: GameState = {
  sectionNumber: 1,
  content: null,
  rules: null,
  decision: null,
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
        Objets: ["Épée", "Bouclier"]
      }
    }
  },
  error: null
};

export const initialStore: GameStore = {
  gameState: initialGameState,
  userResponse: '',
  diceResult: null,
  feedbackMode: false,
  previousSection: null
};
