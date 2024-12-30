import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Choice } from '$lib/types/game';

// Mock browser
vi.mock('$app/environment', () => ({
  browser: true
}));

// Mock gameState with factory function
vi.mock('$lib/stores/gameStore', () => {
  const { writable } = require('svelte/store');
  const store = writable({
    game_id: null,
    session_id: null,
    state: null,
    message: null
  });
  return { gameState: store };
});

// Import after mocks
import { writable, get } from 'svelte/store';
import { WebSocketService } from '../websocketService';
import { gameState } from '$lib/stores/gameStore';

// Mock window
global.window = {
  setInterval: vi.fn(),
  clearInterval: vi.fn()
} as any;

describe('WebSocketService', () => {
  let wsService: WebSocketService;
  let mockWs: any;

  beforeEach(() => {
    // Reset les mocks
    vi.clearAllMocks();

    // Mock WebSocket
    mockWs = {
      send: vi.fn(),
      close: vi.fn(),
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
      readyState: WebSocket.OPEN
    };

    // Mock global WebSocket
    global.WebSocket = vi.fn(() => mockWs);

    // Créer le service sans connexion automatique
    wsService = new WebSocketService('ws://test', false);
  });

  describe('connect', () => {
    it('should establish WebSocket connection', async () => {
      wsService.connect();
      expect(global.WebSocket).toHaveBeenCalledWith('ws://test');
      
      // Simuler une connexion réussie
      mockWs.onopen();
      expect(get(wsService.connectionStatus)).toBe('connected');
    });

    it('should handle connection errors', async () => {
      wsService.connect();
      
      // Simuler une erreur
      mockWs.onerror(new Error('Connection failed'));
      expect(get(wsService.connectionStatus)).toBe('error');
    });
  });

  describe('sendChoice', () => {
    it('should format and send choice correctly', async () => {
      // Connecter d'abord le WebSocket
      wsService.connect();
      mockWs.onopen();
      expect(get(wsService.connectionStatus)).toBe('connected');

      // Set game state
      gameState.set({
        game_id: 'test-game-id',
        session_id: 'test-session',
        state: null,
        message: null
      });

      const testChoice: Choice = {
        text: 'Test choice',
        type: 'direct',
        target_section: 1,
        conditions: [],
        dice_type: 'none',
        dice_results: {}
      };

      await wsService.sendChoice(testChoice);

      expect(mockWs.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'choice',
          choice: {
            game_id: 'test-game-id',
            choice_id: '1',
            choice_text: 'Test choice',
            metadata: {
              type: 'direct',
              target_section: 1,
              conditions: [],
              dice_type: 'none',
              dice_results: {}
            }
          }
        })
      );
    });

    it('should handle disconnected state', async () => {
      wsService.connectionStatus.set('disconnected');

      const testChoice: Choice = {
        text: 'test',
        type: 'direct',
        target_section: 1,
        conditions: [],
        dice_type: 'none',
        dice_results: {}
      };

      await expect(wsService.sendChoice(testChoice))
        .rejects
        .toThrow('WebSocket not connected');
    });

    it('should handle missing game ID', async () => {
      // Connecter d'abord le WebSocket
      wsService.connect();
      mockWs.onopen();
      expect(get(wsService.connectionStatus)).toBe('connected');

      // Set empty game state
      gameState.set({
        game_id: null,
        session_id: null,
        state: null,
        message: null
      });

      const testChoice: Choice = {
        text: 'test',
        type: 'direct',
        target_section: 1,
        conditions: [],
        dice_type: 'none',
        dice_results: {}
      };

      await expect(wsService.sendChoice(testChoice))
        .rejects
        .toThrow('No game ID available');
    });
  });

  describe('disconnect', () => {
    it('should close WebSocket connection', async () => {
      wsService.connect();
      mockWs.onopen();
      
      await wsService.disconnect();
      expect(mockWs.close).toHaveBeenCalled();
      expect(get(wsService.connectionStatus)).toBe('disconnected');
    });
  });

  describe('onMessage', () => {
    it('should handle incoming messages', () => {
      wsService.connect();
      const mockHandler = vi.fn();
      wsService.onMessage(mockHandler);

      // Simuler un message
      const mockData = { type: 'update', state: {} };
      mockWs.onmessage({ data: JSON.stringify(mockData) });

      expect(mockHandler).toHaveBeenCalledWith(mockData);
    });

    it('should handle malformed messages', () => {
      wsService.connect();
      const mockHandler = vi.fn();
      wsService.onMessage(mockHandler);

      // Simuler un message malformé
      mockWs.onmessage({ data: 'invalid json' });

      expect(mockHandler).not.toHaveBeenCalled();
    });
  });
});
