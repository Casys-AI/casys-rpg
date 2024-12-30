import { describe, it, expect, vi, beforeEach } from 'vitest';
import { gameService } from '../gameService';
import { gameSession, gameState, gameChoices } from '$lib/stores/gameStore';
import { get } from 'svelte/store';

describe('GameService', () => {
  beforeEach(() => {
    // Reset les stores
    gameSession.clearSession();
    gameState.reset();
    gameChoices.reset();
    
    // Reset les mocks
    vi.resetAllMocks();
  });

  describe('getGameState', () => {
    it('should return failure response when no game_id exists', async () => {
      const response = await gameService.getGameState();
      expect(response.success).toBe(false);
      expect(response.message).toBe('No game ID found');
    });

    it('should handle 404 response', async () => {
      // Mock gameSession
      gameSession.setSession('test-session', 'invalid-game');
      
      // Mock fetch pour simuler une réponse 404
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ 
          detail: [{ msg: 'Game state not found' }]
        })
      });
      
      // Remplacer la fonction fetch du service
      gameService.setFetch(mockFetch);

      await expect(gameService.getGameState()).rejects.toThrow('Game state not found');
    });

    it('should update stores on successful response', async () => {
      // Mock gameSession
      gameSession.setSession('test-session', 'test-game');
      
      const mockState = {
        success: true,
        message: null,
        session_id: 'test-session',
        game_id: 'test-game',
        state: {
          text: 'Test state',
          choices: [
            { id: 1, text: 'Choice 1' }
          ]
        }
      };

      // Mock fetch pour simuler une réponse réussie
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockState)
      });
      
      // Remplacer la fonction fetch du service
      gameService.setFetch(mockFetch);

      const response = await gameService.getGameState();
      expect(response).toEqual(mockState);
      
      // Vérifier que les stores ont été mis à jour
      expect(get(gameState)).toEqual(mockState.state);
      expect(get(gameChoices).available).toEqual(mockState.state.choices);
    });
  });

  describe('sendChoice', () => {
    it('should update store and send choice via WebSocket', async () => {
      // Mock gameSession
      gameSession.setSession('test-session', 'test-game');
      
      // Mock WebSocket service
      const mockWsService = {
        sendChoice: vi.fn().mockResolvedValue(undefined)
      };
      gameService.wsService = mockWsService as any;

      const mockChoice = {
        text: 'Test choice',
        type: 'direct',
        target_section: 1
      };

      await gameService.sendChoice(mockChoice);
      
      // Vérifier que le choix a été envoyé via WebSocket
      expect(mockWsService.sendChoice).toHaveBeenCalledWith(mockChoice);
    });

    it('should handle WebSocket errors', async () => {
      // Mock gameSession
      gameSession.setSession('test-session', 'test-game');
      
      // Mock WebSocket service avec erreur
      const mockWsService = {
        sendChoice: vi.fn().mockRejectedValue(new Error('WebSocket error'))
      };
      gameService.wsService = mockWsService as any;

      await expect(gameService.sendChoice({ text: 'test' }))
        .rejects.toThrow('WebSocket error');
    });
  });
});
