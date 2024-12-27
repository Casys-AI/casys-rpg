<script>
  import { goto } from '$app/navigation';
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
            Une aventure textuelle unique propulsée par l'intelligence artificielle
          </p>
        </div>
        
        <!-- Features Grid -->
        <div class="mt-20 grid grid-cols-1 gap-12 sm:grid-cols-2 lg:grid-cols-3">
          <div class="rounded-2xl bg-game-background p-8 shadow-neu-flat hover:shadow-neu-pressed transition-all duration-300 animate-slide-in">
            <div class="text-game-primary">
              <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <h3 class="mt-4 text-lg font-medium font-serif">IA Avancée</h3>
              <p class="mt-2 text-game-secondary font-serif">Une expérience narrative unique générée par une IA de pointe</p>
            </div>
          </div>

          <div class="rounded-2xl bg-game-background p-8 shadow-neu-flat hover:shadow-neu-pressed transition-all duration-300 animate-slide-in [animation-delay:200ms]">
            <div class="text-game-primary">
              <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h3 class="mt-4 text-lg font-medium font-serif">Histoire Interactive</h3>
              <p class="mt-2 text-game-secondary font-serif">Vos choix influencent directement le déroulement de l'histoire</p>
            </div>
          </div>

          <div class="rounded-2xl bg-game-background p-8 shadow-neu-flat hover:shadow-neu-pressed transition-all duration-300 animate-slide-in [animation-delay:400ms] sm:col-span-2 lg:col-span-1">
            <div class="text-game-primary">
              <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
              </svg>
              <h3 class="mt-4 text-lg font-medium font-serif">Système Dynamique</h3>
              <p class="mt-2 text-game-secondary font-serif">Un monde qui évolue en fonction de vos actions</p>
            </div>
          </div>
        </div>

        <!-- CTA Button -->
        <div class="mt-16">
          <button
            on:click={() => goto('/game')}
            class="transform rounded-2xl bg-game-background px-12 py-6 text-xl font-serif font-semibold text-game-primary shadow-neu-flat hover:shadow-neu-pressed transition-all duration-300 focus:outline-none"
          >
            Commencer l'aventure
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
