export interface Choice {
  text: string;
  value: string | number;
}

export interface CharacterStats {
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
}

export interface GameState {
  section_number: number;
  current_section: {
    number: number;
    content: string;
    choices: Choice[];
  };
  rules?: {
    needs_dice: boolean;
    dice_type: string;
    conditions: string[];
    next_sections: number[];
    rules_summary: string;
  };
  needs_content: boolean;
  trace: {
    stats: CharacterStats;
    history: any[];
  };
  debug?: boolean;
}
