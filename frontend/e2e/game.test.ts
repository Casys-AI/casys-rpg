import { expect, test } from '@playwright/test';

test.describe('Game Flow', () => {
  test('should handle game initialization and state loading', async ({ page }) => {
    // Aller à la page du jeu
    await page.goto('/game');
    
    // Vérifier que le bouton de démarrage est visible
    const startButton = page.getByRole('button', { name: /commencer/i });
    await expect(startButton).toBeVisible();
    
    // Cliquer sur le bouton et vérifier la redirection
    await startButton.click();
    await expect(page).toHaveURL(/\/game\/read/);
    
    // Vérifier que le contenu du jeu est chargé
    await expect(page.locator('.game-content')).toBeVisible();
    
    // Vérifier que les choix sont affichés
    await expect(page.locator('.choices-container')).toBeVisible();
  });

  test('should handle invalid game state', async ({ page }) => {
    // Simuler un cookie avec un game_id invalide
    await page.context().addCookies([
      {
        name: 'game_id',
        value: 'invalid-game-id',
        url: 'http://localhost:5173'
      }
    ]);

    // Aller à la page de lecture
    await page.goto('/game/read');
    
    // Devrait être redirigé vers /game
    await expect(page).toHaveURL('/game');
  });

  test('should handle choice selection', async ({ page }) => {
    await page.goto('/game');
    
    // Démarrer une nouvelle partie
    await page.getByRole('button', { name: /commencer/i }).click();
    
    // Attendre que les choix soient chargés
    const choicesContainer = page.locator('.choices-container');
    await expect(choicesContainer).toBeVisible();
    
    // Sélectionner le premier choix
    const firstChoice = choicesContainer.locator('.choice').first();
    const choiceText = await firstChoice.textContent();
    await firstChoice.click();
    
    // Vérifier que le choix est marqué comme sélectionné
    await expect(firstChoice).toHaveClass(/selected/);
    
    // Vérifier que l'état du jeu est mis à jour
    await expect(page.locator('.game-content')).toContainText(choiceText || '');
  });

  test('should handle WebSocket reconnection', async ({ page }) => {
    await page.goto('/game/read');
    
    // Simuler une déconnexion WebSocket
    await page.evaluate(() => {
      // @ts-ignore
      window.gameService?.wsService?.ws?.close();
    });
    
    // Vérifier que l'indicateur de déconnexion est affiché
    await expect(page.locator('.connection-status')).toContainText(/déconnecté/i);
    
    // Attendre la reconnexion automatique
    await expect(page.locator('.connection-status')).toContainText(/connecté/i, {
      timeout: 5000
    });
  });
});
