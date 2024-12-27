import { component$, Slot } from '@builder.io/qwik';

export default component$(() => {
  return (
    <div class="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800">
      <Slot />
    </div>
  );
});
