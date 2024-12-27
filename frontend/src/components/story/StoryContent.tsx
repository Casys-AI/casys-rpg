import { component$, $, useSignal, useOnDocument, type QRL } from '@builder.io/qwik';
import type { Choice } from '~/types/game';
import { ActionDialog } from '../dialog/ActionDialog';

interface StoryContentProps {
  content: string;
  choices: Choice[];
  onNavigate$: QRL<(sectionNumber: string) => Promise<any>>;
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

  const handleClick$ = $((e: Event) => {
    const link = (e.target as HTMLElement).closest('a');
    if (!link || !contentRef.value?.contains(link)) return;
    
    const href = link.getAttribute('href');
    if (href?.startsWith('#')) {
      e.preventDefault();
      const sectionNumber = href.substring(1);
      onNavigate$(sectionNumber);
    }
  });

  useOnDocument('click', handleClick$);

  const handleAction$ = $((action: string) => {
    if (onAction$) {
      onAction$(action);
    }
  });

  // Traitement du contenu narratif
  const processContent = (rawContent: any): string => {
    console.log('Raw content received:', rawContent);
    console.log('Type of content:', typeof rawContent);
    
    if (!rawContent) {
      console.log('Content is null or undefined');
      return 'Chargement du contenu...';
    }

    // Si c'est une chaîne de caractères
    if (typeof rawContent === 'string') {
      console.log('Content is string:', rawContent);
      return rawContent;
    }
    
    // Si c'est un objet
    if (typeof rawContent === 'object') {
      console.log('Content is object:', JSON.stringify(rawContent, null, 2));
      
      // Si c'est un NarratorModel ou un objet avec une propriété content
      if (rawContent.content) {
        const content = rawContent.content;
        console.log('Extracted content:', content);
        return content.toString();
      }
    }
    
    // Si aucun format valide n'est trouvé
    console.log('No valid content found, returning empty string');
    return '';
  };

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
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">Erreur! </strong>
        <span class="block sm:inline">{error}</span>
      </div>
    );
  }

  const processedContent = processContent(content);

  return (
    <div class="flex flex-col gap-6 max-w-3xl mx-auto font-primary">
      <div 
        class="
          p-8 leading-relaxed text-gray-800 bg-white 
          rounded-lg shadow-lg prose prose-lg max-w-none
          prose-headings:text-gray-900 prose-headings:font-secondary
          prose-p:text-gray-700 prose-p:font-primary
          prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
        "
        dangerouslySetInnerHTML={{ __html: processedContent }}
        ref={contentRef}
      />

      <ActionDialog 
        message={actionMessage || ''} 
        onSubmit$={handleAction$}
      />

      {choices && choices.length > 0 && (
        <div class="p-6">
          <h3 class="text-xl text-center text-gray-800 mb-6 font-secondary">
            Que souhaitez-vous faire ?
          </h3>
          <ul class="flex flex-col gap-4">
            {choices.map((choice, index) => (
              <li key={index} class="w-full">
                <button 
                  class="
                    w-full text-left p-4 
                    bg-white hover:bg-gray-50 
                    text-gray-700 font-primary text-base
                    rounded-lg shadow-md
                    transition-all duration-200 ease-in-out
                    hover:-translate-y-0.5 active:translate-y-0.5
                    focus:outline-none focus:ring-2 focus:ring-blue-500
                  "
                  onClick$={choice.action}
                >
                  {choice.text}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
});
