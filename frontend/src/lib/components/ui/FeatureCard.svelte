<script lang="ts">
  export let icon: string;
  export let title: string;
  export let description: string;
  export let animationDelay = '0ms';
</script>

<div 
  class="rounded-2xl bg-game-background p-8 shadow-neu-flat hover:shadow-neu-pressed transition-all duration-300 animate-slide-in"
  style="animation-delay: {animationDelay}"
>
  <div class="text-game-primary">
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      class="mx-auto h-12 w-12" 
      fill="none" 
      viewBox="0 0 24 24" 
      stroke="currentColor"
    >
      <path 
        stroke-linecap="round" 
        stroke-linejoin="round" 
        stroke-width="1.5" 
        d={icon}
      />
    </svg>
    <h3 class="mt-4 text-lg font-medium font-serif">{title}</h3>
    <p class="mt-2 text-game-secondary font-serif">{description}</p>
  </div>
</div>
