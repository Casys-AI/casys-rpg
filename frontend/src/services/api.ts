import { API_CONFIG } from '~/config/api';

const API_BASE_URL = API_CONFIG.BASE_URL;
const WS_BASE_URL = API_CONFIG.WS_URL;

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(response.status, errorText || response.statusText);
  }
  return response.json();
}

interface GameStateListener {
  onStateUpdate: (state: any) => void;
  onError: (error: Error) => void;
}

export class GameStateWebSocket {
  private ws: WebSocket | null = null;
  private listeners: GameStateListener[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('📡 WebSocket already connected');
      return;
    }

    const wsUrl = `${WS_BASE_URL}${API_CONFIG.GAME_WS_ENDPOINT}`;
    console.log('🔌 Connecting to WebSocket...');
    console.log(`🔍 WebSocket URL: ${wsUrl}`);
    
    try {
      this.ws = new WebSocket(wsUrl);
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
      this.notifyListeners('onError', new Error('Failed to create WebSocket connection'));
      return;
    }

    this.ws.onmessage = (event) => {
      try {
        console.log('📥 Received WebSocket message:', event.data);
        const state = JSON.parse(event.data);
        
        // Vérifier si c'est une erreur
        if (state.status === 'error') {
          console.error('❌ Server error:', state.error);
          this.notifyListeners('onError', new Error(state.error));
          return;
        }
        
        // Vérifier que l'état est valide
        if (!state.section_number || !state.current_section) {
          console.error('❌ Invalid game state:', state);
          this.notifyListeners('onError', new Error('Invalid game state received'));
          return;
        }
        
        this.notifyListeners('onStateUpdate', state);
      } catch (error) {
        console.error('❌ Failed to parse WebSocket message:', error);
        this.notifyListeners('onError', new Error('Failed to parse game state'));
      }
    };

    this.ws.onclose = () => {
      console.log('🔌 WebSocket connection closed');
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})...`);
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, delay);
      } else {
        console.error('❌ Max reconnection attempts reached');
        this.notifyListeners('onError', new Error('WebSocket connection failed after max retries'));
      }
    };

    this.ws.onerror = (error) => {
      console.error('💥 WebSocket error:', error);
      this.notifyListeners('onError', new Error('WebSocket connection error'));
    };

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected successfully');
      this.reconnectAttempts = 0;
      this.notifyListeners('onStateUpdate', null); // Signal successful connection
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
