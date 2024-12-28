<script lang="ts">
  import Card from '../ui/Card.svelte';
  
  export let message: string;
  export let animated = true;
</script>

<div class="mx-auto max-w-md">
  <Card 
    className="bg-game-error/5"
    {animated}
  >
    <p class="text-game-error font-serif">{message}</p>
  </Card>
</div>
