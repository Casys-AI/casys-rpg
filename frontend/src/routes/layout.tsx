import { component$, Slot } from '@builder.io/qwik';

export default component$(() => {
  return (
    <div class="min-h-screen bg-gray-900">
      <main class="container mx-auto">
        <Slot />
      </main>
    </div>
  );
});
