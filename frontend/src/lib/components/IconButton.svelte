<!-- Icon Button with Tooltip Component -->
<script lang="ts">
    export let tooltip: string = '';
    export let onClick: () => void;
    export let active: boolean = false;
</script>

<button
    on:click={onClick}
    class="relative p-2 rounded-full hover:bg-game-surface/10 transition-colors group"
    aria-label={tooltip}
>
    <slot />
    {#if tooltip}
        <div class="absolute hidden group-hover:block bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-sm font-serif bg-game-surface/95 backdrop-blur-sm text-game-primary rounded shadow-neu-flat whitespace-nowrap">
            {tooltip}
        </div>
    {/if}
</button>
