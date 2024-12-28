<script lang="ts">
  import { onMount } from 'svelte';
  import type { HTMLInputAttributes } from 'svelte/elements';

  interface $$Props extends HTMLInputAttributes {
    label?: string;
  }

  export let label: $$Props['label'] = undefined;
  export let value: $$Props['value'] = '';
  export let type: $$Props['type'] = 'text';
  export let required: $$Props['required'] = false;
  export let placeholder: $$Props['placeholder'] = '';

  let inputElement: HTMLInputElement;
  let focused = false;
  let mounted = false;

  onMount(() => {
    mounted = true;
  });

  $: labelFloating = mounted && (focused || value !== '');
</script>

<div class="container flex flex-col gap-7 relative text-white">
  <input
    bind:this={inputElement}
    {type}
    {value}
    {required}
    {placeholder}
    on:focus={() => focused = true}
    on:blur={() => focused = false}
    class="input w-[200px] h-[45px] border-none outline-none px-2 rounded-md text-white text-[15px] bg-transparent shadow-input-dark dark:shadow-input-dark focus:shadow-input-dark-focus dark:focus:shadow-input-dark-focus transition-shadow duration-300"
    {...$$restProps}
  />
  
  {#if label}
    <label
      for={inputElement?.id}
      class="label text-[15px] pl-[10px] absolute top-[13px] transition-all duration-300 pointer-events-none {
        labelFloating ? 'animate-label-float' : ''
      }"
    >
      {label}
    </label>
  {/if}
</div>

<style>
  .input:focus {
    border: 2px solid transparent;
  }

  /* Pour assurer que le label reste en haut quand l'input est valide ou focus */
  .input:valid ~ .label,
  .input:focus ~ .label {
    transform: translateY(-35px);
    padding-left: 2px;
  }
</style>
