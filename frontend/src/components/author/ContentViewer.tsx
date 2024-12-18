import { component$, useSignal, useTask$, $ } from '@builder.io/qwik';

export const ContentViewer = component$(() => {
  const content = useSignal<string>('');
  const title = useSignal<string>('');

  // Listen for section selection events using useTask$
  useTask$(({ cleanup }) => {
    if (typeof window === 'undefined') return;

    const handleSectionSelected = (event: Event) => {
      const customEvent = event as CustomEvent;
      const section = customEvent.detail;
      content.value = section.content;
      title.value = section.title;
    };

    // Add event listener
    window.addEventListener('section-selected', handleSectionSelected);

    // Cleanup function to remove event listener
    cleanup(() => {
      window.removeEventListener('section-selected', handleSectionSelected);
    });
  });

  return (
    <div class="h-full">
      {title.value ? (
        <>
          <h1 class="text-2xl font-bold mb-4">{title.value}</h1>
          <div class="prose max-w-none">
            {/* Add markdown rendering here if needed */}
            {content.value}
          </div>
        </>
      ) : (
        <div class="flex items-center justify-center h-full text-gray-500">
          Sélectionnez une section pour afficher son contenu
        </div>
      )}
    </div>
  );
});
