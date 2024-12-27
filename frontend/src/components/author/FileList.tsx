import { component$, useSignal, useStore, useTask$, $ } from '@builder.io/qwik';

interface Section {
  id: string;
  title: string;
  content: string;
}

export const FileList = component$(() => {
  const sections = useStore<Section[]>([]);
  const loading = useSignal(false);
  const error = useSignal<string | null>(null);
  const selectedSection = useSignal<string | null>(null);

  // Fetch sections from API
  useTask$(async () => {
    if (typeof window === 'undefined') return;
    
    loading.value = true;
    try {
      // TODO: Implement API call
      const mockData: Section[] = [
        { id: '1', title: 'Introduction', content: 'Introduction content' },
        { id: '2', title: 'Chapter 1', content: 'Chapter 1 content' }
      ];
      sections.length = 0;
      sections.push(...mockData);
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Error fetching sections';
      console.error('Error fetching sections:', err);
    } finally {
      loading.value = false;
    }
  });

  // Handle section selection
  const handleSectionClick$ = $((section: Section) => {
    selectedSection.value = section.id;
    // Emit event to update content viewer
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('section-selected', {
          detail: section,
        })
      );
    }
  });

  return (
    <div class="h-full">
      <h2 class="text-lg font-semibold mb-4">Sections</h2>
      {loading.value ? (
        <div class="flex items-center justify-center p-4">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : error.value ? (
        <div class="text-red-500 p-4">{error.value}</div>
      ) : (
        <ul class="space-y-2">
          {sections.map((section) => (
            <li
              key={section.id}
              class={`
                cursor-pointer p-2 rounded
                ${selectedSection.value === section.id
                  ? 'bg-blue-100 text-blue-800'
                  : 'hover:bg-gray-100'
                }
              `}
              onClick$={() => handleSectionClick$(section)}
            >
              {section.title}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
});
