<script lang="ts">
  export let title: string;
  export let subtitle: string | undefined = undefined;
  export let animated = true;
</script>

<div class="text-center">
  <div class={`space-y-8 py-20 ${animated ? 'animate-fade-in' : ''}`}>
    <div class={animated ? 'animate-float' : ''}>
      <h1 class="text-6xl font-serif font-extrabold text-game-primary tracking-tight">
        {title}
      </h1>
      {#if subtitle}
        <p class="mx-auto mt-3 max-w-md text-xl text-game-secondary font-serif">
          {subtitle}
        </p>
      {/if}
    </div>
    <slot />
  </div>
</div>
