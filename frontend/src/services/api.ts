import { API_CONFIG, updateApiConfig } from '~/config/api';

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
  private isConnecting = false;

  async connect() {
    if (this.isConnecting) {
      console.log('🔄 Already attempting to connect...');
      return;
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('📡 WebSocket already connected');
      return;
    }

    this.isConnecting = true;

    try {
      // Mise à jour de la configuration pour obtenir le bon port
      const config = await updateApiConfig();
      const wsUrl = `${config.WS_URL}${config.GAME_WS_ENDPOINT}`;
      console.log('🔌 Connecting to WebSocket...', wsUrl);

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.listeners.forEach(listener => listener.onStateUpdate(null));
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach(listener => listener.onStateUpdate(data));
        } catch (err) {
          console.error('❌ Error parsing WebSocket message:', err);
          const error = new Error('Erreur de décodage des données du serveur');
          this.listeners.forEach(listener => listener.onError(error));
        }
      };

      this.ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        const error = new Error('Erreur de connexion au serveur de jeu');
        this.listeners.forEach(listener => listener.onError(error));
      };

      this.ws.onclose = () => {
        console.log('❌ WebSocket closed');
        this.isConnecting = false;
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
          setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        } else {
          const error = new Error('La connexion au serveur a été perdue. Veuillez réessayer plus tard.');
          this.listeners.forEach(listener => listener.onError(error));
        }
      };

    } catch (err) {
      console.error('❌ Error connecting to WebSocket:', err);
      this.isConnecting = false;
      const error = new Error('Impossible de se connecter au serveur de jeu. Veuillez vérifier votre connexion.');
      this.listeners.forEach(listener => listener.onError(error));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  addListener(listener: GameStateListener) {
    this.listeners.push(listener);
  }

  removeListener(listener: GameStateListener) {
    this.listeners = this.listeners.filter(l => l !== listener);
  }

  private notifyListeners(event: keyof GameStateListener, data: any) {
    this.listeners.forEach(listener => {
      try {
        listener[event](data);
      } catch (error) {
        console.error(`Error in listener ${event}:`, error);
      }
    });
  }
}

export const gameStateWS = new GameStateWebSocket();

export const api = {
  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.HEALTH_CHECK_ENDPOINT}`);
    return handleResponse(response);
  },

  async checkAuthorHealth() {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.HEALTH_CHECK_ENDPOINT}?check_type=author`);
    return handleResponse(response);
  },

  async getGameState() {
    const response = await fetch(`${API_BASE_URL}/api/game/state`);
    return handleResponse(response);
  },

  async getSections() {
    const response = await fetch(`${API_BASE_URL}/api/game/sections`);
    return handleResponse(response);
  },

  async getKnowledgeGraph() {
    const response = await fetch(`${API_BASE_URL}/api/game/knowledge-graph`);
    return handleResponse(response);
  },

  async processAction(action: { user_response: string; dice_result?: number }) {
    const response = await fetch(`${API_BASE_URL}/api/game/action`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(action),
    });
    return handleResponse(response);
  },

  async rollDice(diceType: string) {
    const response = await fetch(`${API_BASE_URL}/api/game/roll/${diceType}`);
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
    const response = await fetch(`${API_BASE_URL}/api/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedback),
    });
    return handleResponse(response);
  },
};
