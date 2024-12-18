const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }
  return response.json();
}

interface GameStateListener {
  onStateUpdate: (state: any) => void;
  onError: (error: Error) => void;
}

class GameStateWebSocket {
  private ws: WebSocket | null = null;
  private listeners: GameStateListener[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(`${WS_BASE_URL}/ws/game`);

    this.ws.onmessage = (event) => {
      try {
        const state = JSON.parse(event.data);
        this.notifyListeners('onStateUpdate', state);
      } catch (error) {
        this.notifyListeners('onError', new Error('Failed to parse game state'));
      }
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
      } else {
        this.notifyListeners('onError', new Error('WebSocket connection failed'));
      }
    };

    this.ws.onerror = () => {
      this.notifyListeners('onError', new Error('WebSocket error occurred'));
    };
  }

  private notifyListeners(event: keyof GameStateListener, data: any) {
    this.listeners.forEach(listener => {
      listener[event](data);
    });
  }

  addListener(listener: GameStateListener) {
    this.listeners.push(listener);
  }

  removeListener(listener: GameStateListener) {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners = [];
    this.reconnectAttempts = 0;
  }
}

export const gameStateWS = new GameStateWebSocket();

export const api = {
  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse(response);
  },

  async checkAuthorHealth() {
    const response = await fetch(`${API_BASE_URL}/author/health`);
    return handleResponse(response);
  },

  // Note: Cette méthode est conservée pour la compatibilité, mais il est recommandé
  // d'utiliser gameStateWS pour les mises à jour en temps réel
  async getGameState() {
    const response = await fetch(`${API_BASE_URL}/game/state`);
    return handleResponse(response);
  },

  async getSections() {
    const response = await fetch(`${API_BASE_URL}/sections`);
    return handleResponse(response);
  },

  async getKnowledgeGraph() {
    const response = await fetch(`${API_BASE_URL}/graph`);
    return handleResponse(response);
  },

  async processAction(action: { user_response: string; dice_result?: number }) {
    const response = await fetch(`${API_BASE_URL}/game/action`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(action),
    });
    return handleResponse(response);
  },

  async rollDice(diceType: string) {
    const response = await fetch(`${API_BASE_URL}/game/roll/${diceType}`);
    return handleResponse(response);
  },

  async submitFeedback(feedback: {
    content: string;
    feedback_type?: string;
    current_section: number;
    game_state: any;
    trace_history?: any[];
    session_id: string;
    user_id?: string;
  }) {
    const response = await fetch(`${API_BASE_URL}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedback),
    });
    return handleResponse(response);
  },
};
