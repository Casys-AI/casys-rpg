<script lang="ts">
  import type { HTMLButtonAttributes } from 'svelte/elements';
  
  interface $$Props extends HTMLButtonAttributes {
    variant?: 'primary' | 'secondary';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
    icon?: string;
  }

  export let variant: $$Props['variant'] = 'primary';
  export let size: $$Props['size'] = 'md';
  export let loading: $$Props['loading'] = false;
  export let icon: $$Props['icon'] = undefined;
  export let type: HTMLButtonAttributes['type'] = 'button';
  export let disabled: HTMLButtonAttributes['disabled'] = false;

  const baseClasses = "relative cursor-pointer border transition-all duration-300 focus:outline-none flex items-center justify-center font-serif";
  
  const sizeClasses = {
    sm: "px-4 py-2 text-base",
    md: "px-6 py-3 text-lg",
    lg: "px-8 py-4 text-xl"
  };
  
  const variantClasses = {
    primary: "bg-game-card-light dark:bg-game-card-dark text-game-primary-light dark:text-game-primary-dark border-game-card-light dark:border-game-card-dark shadow-neu-flat-light dark:shadow-neu-flat-dark hover:shadow-neu-pressed-light dark:hover:shadow-neu-pressed-dark active:shadow-neu-pressed-light dark:active:shadow-neu-pressed-dark disabled:opacity-50 disabled:cursor-not-allowed",
    secondary: "bg-game-card-light/90 dark:bg-game-card-dark/90 text-game-secondary-light dark:text-game-secondary-dark border-game-card-light/90 dark:border-game-card-dark/90 shadow-neu-flat-light dark:shadow-neu-flat-dark hover:shadow-neu-pressed-light dark:hover:shadow-neu-pressed-dark active:shadow-neu-pressed-light dark:active:shadow-neu-pressed-dark disabled:opacity-50 disabled:cursor-not-allowed"
  };

  $: classes = `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} rounded-lg`;
</script>

<button
  {type}
  {disabled}
  class={classes}
  on:click
  {...$$restProps}
>
  {#if loading}
    <svg class="h-5 w-5 animate-pulse-slow" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  {:else if icon}
    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={icon} />
    </svg>
  {/if}
  <span>
    <slot>Button</slot>
  </span>
</button>
