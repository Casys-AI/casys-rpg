import { component$, useSignal, $ } from "@builder.io/qwik";
import type { QRL } from "@builder.io/qwik";
import type { Choice } from '~/types/game';
import { ActionDialog } from '../dialog/ActionDialog';

interface StoryContentProps {
  content: string;
  choices?: Choice[];
  onNavigate$?: QRL<(sectionNumber: string) => Promise<void>>;
}

interface ContentSignals {
  dialogOpen: boolean;
  dialogMessage: string;
  scrollPosition: number;
}

export const StoryContent = component$<StoryContentProps>(({ 
  content, 
  choices = [], 
  onNavigate$ 
}) => {
  const contentRef = useSignal<HTMLDivElement>();
  const signals = useSignal<ContentSignals>({
    dialogOpen: false,
    dialogMessage: '',
    scrollPosition: 0
  });

  // Gestion de la boîte de dialogue
  const showDialog = $((message: string) => {
    signals.value = {
      ...signals.value,
      dialogMessage: message,
      dialogOpen: true
    };
  });

  const closeDialog = $(() => {
    signals.value = {
      ...signals.value,
      dialogOpen: false
    };
  });

  // Gestion des clics sur les liens
  const handleClick$ = $((e: Event) => {
    const link = (e.target as HTMLElement).closest('a');
    if (!link || !contentRef.value?.contains(link)) return;
    
    const href = link.getAttribute('href');
    if (href?.startsWith('#') && onNavigate$) {
      e.preventDefault();
      const sectionNumber = href.substring(1);
      
      // Sauvegarder la position de défilement
      signals.value = {
        ...signals.value,
        scrollPosition: window.scrollY
      };
      
      onNavigate$(sectionNumber);
    }
  });

  return (
    <div class="max-w-3xl mx-auto py-8 px-4 bg-white dark:bg-gray-900">
      {/* Contenu principal */}
      <div
        ref={contentRef}
        class="prose prose-lg dark:prose-invert mx-auto text-justify space-y-6"
        dangerouslySetInnerHTML={content}
        onClick$={handleClick$}
      />

      {/* Liste des choix */}
      {choices.length > 0 && (
        <div class="mt-12 space-y-6">
          <h2 class="text-2xl font-bold text-center text-gray-900 dark:text-gray-100">
            Que souhaitez-vous faire ?
          </h2>
          <div class="space-y-4">
            {choices.map((choice) => (
              <button
                key={choice.target}
                onClick$={() => onNavigate$?.(choice.target)}
                class="w-full text-left p-4 rounded-lg bg-gray-100 dark:bg-gray-800 
                       shadow-md hover:shadow-lg transition-all duration-200
                       text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700"
              >
                {choice.text}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Boîte de dialogue */}
      <ActionDialog
        isOpen={signals.value.dialogOpen}
        message={signals.value.dialogMessage}
        onClose$={closeDialog}
      />
    </div>
  );
});
