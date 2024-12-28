<script lang="ts">
  export let animated = true;
  export let subtitle: string | undefined = undefined;
</script>

<div class={animated ? 'animate-float' : ''}>
  <h1 class="text-6xl font-serif font-extrabold text-game-primary tracking-tight">
    CASYS RPG
  </h1>
  {#if subtitle}
    <p class="mx-auto mt-3 max-w-md text-xl text-game-secondary font-serif">
      {subtitle}
    </p>
  {/if}
</div>
