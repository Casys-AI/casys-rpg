import { createContextId } from '@builder.io/qwik';

export interface CharacterStats {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  health: number;
  maxHealth: number;
  experience: number;
}

export interface GameState {
  currentSection: number;
  character: CharacterStats;
  inventory: string[];
  visitedSections: number[];
  flags: Record<string, boolean>;
}

export const GameStateContext = createContextId<GameState>('game-state');

export const initialGameState: GameState = {
  currentSection: 1,
  character: {
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10,
    health: 100,
    maxHealth: 100,
    experience: 0,
  },
  inventory: [],
  visitedSections: [],
  flags: {},
};
