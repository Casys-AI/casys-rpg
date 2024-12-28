<script lang="ts">
  import type { HTMLButtonAttributes } from 'svelte/elements';
  
  interface $$Props extends HTMLButtonAttributes {
    icon?: string;
  }

  export let icon: $$Props['icon'] = undefined;
  export let type: HTMLButtonAttributes['type'] = 'button';
  export let disabled: HTMLButtonAttributes['disabled'] = false;
</script>

<button
  {type}
  {disabled}
  class="styled-button relative px-8 py-4 text-lg font-bold text-white bg-styled-gradient rounded-full cursor-pointer shadow-styled transition-all duration-200 inline-flex items-center justify-center border border-styled-border active:translate-y-0.5 active:shadow-styled-pressed"
  on:click
  {...$$restProps}
>
  <span class="relative z-10">
    <slot>Button</slot>
  </span>
  
  {#if icon}
    <span class="inner-button relative flex items-center justify-center bg-styled-gradient w-10 h-10 ml-2.5 rounded-full shadow-styled-inner border border-[#252525] transition-all duration-200">
      <svg
        class="icon w-6 h-6 text-white drop-shadow-styled hover:drop-shadow-styled-hover transition-all duration-400 ease-in-out hover:rotate-[-35deg]"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d={icon} />
      </svg>
    </span>
  {/if}
</button>

<style>
  .styled-button::before {
    @apply content-[''] absolute -top-0.5 -right-px -bottom-px -left-px bg-styled-border -z-10 rounded-full transition-all duration-200 opacity-100;
  }

  .inner-button::before {
    @apply content-[''] absolute -top-0.5 -right-px -bottom-px -left-px bg-styled-border -z-10 rounded-full transition-all duration-200 opacity-100;
  }
</style>
