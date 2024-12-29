<script lang="ts">
  import { onMount } from 'svelte';

  let checked = false;
  let mounted = false;

  onMount(() => {
    if (typeof document !== 'undefined') {
      checked = document.documentElement.classList.contains('dark');
      mounted = true;
    }
  });

  function toggleTheme() {
    if (typeof document === 'undefined') return;
    checked = !checked;
    if (checked) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }
</script>

<div class="container w-28 h-28 relative">
  <input
    type="checkbox"
    bind:checked
    on:change={toggleTheme}
    class="hidden"
    id="themeToggle"
  />
  <label
    for="themeToggle"
    class="button absolute w-full h-full rounded-full border-4 border-game-toggle-darker bg-transparent bg-toggle-gradient-new shadow-toggle flex items-center justify-center {checked ? 'checked' : ''}"
  >
    <span class="icon w-[60px] h-[60px] inline-block">
      {#if mounted}
        <svg
          class="w-full h-full {checked ? 'fill-game-accent animate-fill' : 'fill-game-toggle-icon'}"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          {#if checked}
            <!-- Moon icon -->
            <path d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
          {:else}
            <!-- Sun icon -->
            <path d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
          {/if}
        </svg>
      {/if}
    </span>
  </label>
</div>

<style>
  .button::before {
    @apply absolute content-[''] w-[116px] h-[116px] rounded-full bg-transparent bg-toggle-outer-new -z-10 shadow-toggle-outer;
  }

  .button.checked {
    @apply shadow-toggle-checked border-game-accent border-opacity-30 animate-border;
  }
</style>
