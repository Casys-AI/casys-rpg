import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WebSocketService } from '../websocketService';
import { browser } from '$app/environment';

// Mock browser et window
vi.mock('$app/environment', () => ({
  browser: false
}));

// Mock global window
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
      expect(wsService.getConnectionStatus()).toBe('connected');
    });

    it('should handle connection errors', async () => {
      wsService.connect();
      
      // Simuler une erreur
      mockWs.onerror(new Error('Connection failed'));
      expect(wsService.getConnectionStatus()).toBe('error');
    });
  });

  describe('sendChoice', () => {
    it('should format and send choice correctly', async () => {
      wsService.connect();
      mockWs.onopen();

      const mockChoice = {
        text: 'Test choice',
        type: 'direct',
        target_section: 1
      };

      await wsService.sendChoice(mockChoice);

      expect(mockWs.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'choice',
          choice: mockChoice.text
        })
      );
    });

    it('should handle disconnected state', async () => {
      wsService.connect();
      
      // Simuler une déconnexion
      mockWs.readyState = WebSocket.CLOSED;
      wsService.connectionStatus.set('disconnected');
      
      await expect(wsService.sendChoice({ text: 'test' }))
        .rejects
        .toThrow('WebSocket not connected');
    });
  });

  describe('disconnect', () => {
    it('should close WebSocket connection', async () => {
      wsService.connect();
      mockWs.onopen();
      
      await wsService.disconnect();
      expect(mockWs.close).toHaveBeenCalled();
      expect(wsService.getConnectionStatus()).toBe('disconnected');
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
