<script lang="ts">
  export let hover = false;
  export let animated = false;
  export let size: 'sm' | 'md' | 'lg' = 'md';

  $: classes = `bg-game-card-light dark:bg-game-card-dark shadow-card-light dark:shadow-card-dark rounded-[30px] transition-all duration-300 ${
    size === 'sm' ? 'w-[190px] h-[254px]' :
    size === 'lg' ? 'w-[380px] h-[508px]' :
    'w-[285px] h-[381px]'
  } ${
    hover ? 'hover:scale-105' : ''
  } ${
    animated ? 'animate-slide-in' : ''
  }`;
</script>

<div 
  class={classes} 
  {...$$restProps}
>
  <div class="p-8 h-full flex flex-col">
    <slot />
  </div>
</div>

<style>
  :global(.dark) .card {
    background: #212121;
    box-shadow: 15px 15px 30px rgb(25, 25, 25),
                -15px -15px 30px rgb(60, 60, 60);
  }
</style>
