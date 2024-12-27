import { component$, $, useSignal, useOnDocument, type QRL } from '@builder.io/qwik';
import type { Choice } from '~/types/game';
import { ActionDialog } from '../dialog/ActionDialog';

interface StoryContentProps {
  content: string;
  choices?: Choice[];
  onNavigate$?: QRL<(sectionNumber: string) => Promise<any>>;
  actionMessage?: string;
  onAction$?: QRL<(action: string) => void>;
  loading?: boolean;
  error?: string;
}

export const StoryContent = component$<StoryContentProps>(({ 
  content, 
  choices = [], 
  onNavigate$, 
  actionMessage,
  onAction$,
  loading,
  error 
}) => {
  const dialogOpen = useSignal(false);
  const dialogMessage = useSignal('');
  const contentRef = useSignal<HTMLDivElement>();

  // Fonction pour afficher un message dans la boîte de dialogue
  const showDialog = $((message: string) => {
    dialogMessage.value = message;
    dialogOpen.value = true;
  });

  // Fonction pour fermer la boîte de dialogue
  const closeDialog = $(() => {
    dialogOpen.value = false;
  });

  // Gestion des clics sur les liens
  const handleClick$ = $((e: Event) => {
    const link = (e.target as HTMLElement).closest('a');
    if (!link || !contentRef.value?.contains(link)) return;
    
    const href = link.getAttribute('href');
    if (href?.startsWith('#') && onNavigate$) {
      e.preventDefault();
      const sectionNumber = href.substring(1);
      onNavigate$(sectionNumber);
    }
  });

  useOnDocument('click', handleClick$);

  // Si chargement
  if (loading) {
    return (
      <div class="flex justify-center items-center h-64">
        <div class="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-gray-900">
          <span class="sr-only">Chargement...</span>
        </div>
      </div>
    );
  }

  // Si erreur
  if (error) {
    return (
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
        <strong class="font-bold">Erreur : </strong>
        <span class="block sm:inline">{error}</span>
      </div>
    );
  }

  // Si pas de contenu
  if (!content) {
    return (
      <div class="text-center py-8">
        <p class="text-gray-600">Aucun contenu disponible</p>
      </div>
    );
  }

  return (
    <div class="pt-8">
      {/* Contenu narratif */}
      <div 
        class="max-w-3xl mx-auto text-justify leading-relaxed mb-8 whitespace-pre-wrap bg-white text-gray-900 p-8 rounded-lg shadow-sm"
        ref={contentRef}
      >
        {content}
      </div>
      
      {/* Choix disponibles */}
      {choices && choices.length > 0 && (
        <div class="max-w-3xl mx-auto mt-8 space-y-4 bg-white p-6 rounded-lg shadow-sm">
          {choices.map((choice) => (
            <button
              key={choice.target}
              class="w-full text-left px-6 py-3 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg transition-colors"
              onClick$={() => onNavigate$?.(choice.target)}
            >
              {choice.text}
            </button>
          ))}
        </div>
      )}

      {/* Feedback */}
      <div class="max-w-3xl mx-auto mt-8 p-6 border-t border-gray-200 bg-white rounded-lg shadow-sm">
        <p class="text-gray-900 mb-4">Comment trouvez-vous ce passage ?</p>
        <div class="flex space-x-4">
          <button
            class="px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
            onClick$={() => showDialog('Merci pour votre retour positif !')}
          >
            👍 J'aime
          </button>
          <button
            class="px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
            onClick$={() => showDialog('Merci pour votre retour, nous allons l\'analyser.')}
          >
            👎 Je n'aime pas
          </button>
        </div>
      </div>

      {/* Boîte de dialogue pour les actions */}
      {actionMessage && (
        <ActionDialog
          open={dialogOpen.value}
          message={dialogMessage.value}
          onClose={closeDialog}
          onAction={onAction$}
        />
      )}
    </div>
  );
});
