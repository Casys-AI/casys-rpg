<script lang="ts">
  export let path: string;
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let className = '';

  const sizeMap = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-12 w-12'
  };

  $: classes = `${sizeMap[size]} ${className}`;
</script>

<svg 
  xmlns="http://www.w3.org/2000/svg" 
  class={classes} 
  fill="none" 
  viewBox="0 0 24 24" 
  stroke="currentColor"
  {...$$restProps}
>
  <path 
    stroke-linecap="round" 
    stroke-linejoin="round" 
    stroke-width="1.5" 
    d={path}
  />
</svg>
