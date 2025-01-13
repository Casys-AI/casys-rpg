<!-- Knowledge Graph Component -->
<script lang="ts">
    export let show: boolean = false;
</script>

{#if show}
    <div class="fixed right-0 top-[4rem] bottom-0 w-80 bg-game-surface/95 backdrop-blur-sm shadow-neu-flat transform transition-all duration-300 ease-in-out overflow-y-auto">
        <div class="p-4">
            <h2 class="text-lg font-serif font-medium text-game-primary mb-4">Knowledge Graph</h2>
            <!-- Placeholder pour le graph -->
            <div class="h-full w-full bg-game-background/30 rounded-lg p-4">
                <p class="text-game-secondary">Knowledge Graph placeholder</p>
            </div>
        </div>
    </div>
{/if}
