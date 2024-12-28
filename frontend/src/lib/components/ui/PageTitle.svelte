<script lang="ts">
  export let title: string;
  export let subtitle: string | undefined = undefined;
  export let animated = true;
</script>

<div class:animate-fade-in={animated}>
  <div class:animate-float={animated}>
    <h1 class="text-6xl font-serif font-extrabold text-game-primary tracking-tight">
      {title}
    </h1>
    {#if subtitle}
      <p class="mx-auto mt-3 max-w-md text-xl text-game-secondary font-serif">
        {subtitle}
      </p>
    {/if}
  </div>
</div>
