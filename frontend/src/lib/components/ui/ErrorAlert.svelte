<script lang="ts">
  export let message: string;
  export let centered = true;
</script>

<div class:mx-auto={centered} class="max-w-md">
  <div class="rounded-2xl bg-game-error/5 p-6 shadow-neu-flat animate-slide-in">
    <p class="text-game-error font-serif">{message}</p>
  </div>
</div>
