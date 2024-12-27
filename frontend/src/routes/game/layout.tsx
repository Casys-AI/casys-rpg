import { component$, Slot } from '@builder.io/qwik';

export default component$(() => {
  return (
    <div class="game-layout">
      <Slot />
    </div>
  );
});
