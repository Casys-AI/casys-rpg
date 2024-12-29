<script lang="ts">
  import { goto } from '$app/navigation';
  import { gameService } from '$lib/services/gameService';

  let loading = false;
  let error: string | null = null;

  async function handleStartGame() {
    loading = true;
    error = null;

    try {
      // Initialiser le jeu via l'API backend
      const response = await gameService.initialize();
      console.log('🎲 Game initialized in component:', response);
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to initialize game');
      }
      
      // Rediriger vers la page de jeu
      goto('/game/read');
    } catch (e) {
      console.error('Game initialization error:', e);
      error = e instanceof Error ? e.message : 'Une erreur est survenue lors de l\'initialisation du jeu';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen bg-game-background">
  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
    <div class="text-center">
      <!-- Hero Section -->
      <div class="animate-fade-in space-y-8 py-20">
        <div class="animate-float">
          <h1 class="text-6xl font-serif font-extrabold text-game-primary tracking-tight">
            CASYS RPG
          </h1>
          <p class="mx-auto mt-3 max-w-md text-xl text-game-secondary font-serif">
            Prêt pour l'aventure ?
          </p>
        </div>

        {#if error}
          <div class="mx-auto max-w-md">
            <div class="rounded-2xl bg-game-error/5 p-6 shadow-neu-flat animate-slide-in">
              <p class="text-game-error font-serif">{error}</p>
            </div>
          </div>
        {/if}

        <!-- CTA Button -->
        <div class="mt-16">
          <button
            on:click={handleStartGame}
            disabled={loading}
            class="transform rounded-2xl bg-game-background px-12 py-6 text-xl font-serif font-semibold text-game-primary shadow-neu-flat hover:bg-opacity-95 active:shadow-neu-pressed transition-all duration-300 focus:outline-none disabled:opacity-50 flex mx-auto items-center space-x-3"
          >
            {#if loading}
              <svg class="h-6 w-6 animate-pulse-slow" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            {/if}
            <span>{loading ? 'Initialisation...' : 'Commencer l\'aventure'}</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <footer class="py-8 mt-20">
    <div class="text-center text-game-secondary font-serif">
      <p> 2024 CASYS RPG - Une expérience narrative unique</p>
    </div>
  </footer>
</div>
