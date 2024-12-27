interface Choice {
    text: string;
    type: string;
    target_section: number;
    conditions: any[];
    dice_type: string;
    dice_results: Record<string, any>;
}

interface Rules {
    section_number: number;
    dice_type: string;
    needs_dice: boolean;
    needs_user_response: boolean;
    next_action: string;
    conditions: any[];
    choices: Choice[];
    rules_summary: string;
    error: string | null;
    source: string;
    source_type: string;
    last_update: string;
}

interface Narrative {
    section_number: number;
    content: string;
    source_type: string;
    error: string | null;
    timestamp: string;
    last_update: string;
}

interface GameState {
    session_id: string;
    game_id: string;
    narrative: Narrative;
    rules: Rules;
    trace: any | null;
    character: any | null;
    decision: any | null;
    error: string | null;
    section_number: number;
    player_input: string | null;
    content: string | null;
}

export interface GameResponse {
    game_id: string;
    state: GameState;
    message: string | null;
}
