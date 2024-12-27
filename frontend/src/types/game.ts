export interface Choice {
  text: string;
  target: string;
}

export interface NarrativeState {
  section_number: number;
  content: string;
  source_type: string;
  error: string | null;
  timestamp: string;
  last_update: string;
}

export interface RulesState {
  needs_dice: boolean;
  dice_type: string;
}

export interface GameState {
  session_id: string;
  game_id: string;
  narrative: NarrativeState;
  rules: RulesState;
  choices: Choice[];
}
