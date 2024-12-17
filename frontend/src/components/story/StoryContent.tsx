import { component$, useStyles$, $, useSignal, useOnDocument, type QRL } from '@builder.io/qwik';
import type { Choice } from '~/types/game';
import { ActionDialog } from '../dialog/ActionDialog';

interface StoryContentProps {
  content: string;
  choices: Choice[];
  onNavigate$: QRL<(sectionNumber: string) => Promise<any>>;
  actionMessage?: string;
  onAction$?: (action: string) => void;
}

export const StoryContent = component$<StoryContentProps>(({ 
  content, 
  choices, 
  onNavigate$, 
  actionMessage,
  onAction$ 
}) => {
  const dialogOpen = useSignal(false);
  const dialogMessage = useSignal('');

  // Fonction pour afficher un message dans la boîte de dialogue
  const showDialog = $((message: string) => {
    dialogMessage.value = message;
    dialogOpen.value = true;
  });

  // Fonction pour fermer la boîte de dialogue
  const closeDialog = $(() => {
    dialogOpen.value = false;
  });

  useStyles$(`
    .story-content {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-lg);
      max-width: 800px;
      margin: 0 auto;
      font-family: var(--font-primary);
    }

    .content-text {
      padding: var(--spacing-xl);
      line-height: 1.8;
      color: var(--color-ink);
      background: var(--color-paper);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-soft);
    }

    .content-text h1 {
      font-family: var(--font-secondary);
      font-size: 2rem;
      margin-bottom: var(--spacing-lg);
      text-align: center;
      color: var(--color-ink-dark);
    }

    .content-text p {
      margin-bottom: var(--spacing-md);
      text-align: justify;
      font-size: 1.1rem;
    }

    .content-text em {
      color: var(--color-ink-dark);
      font-style: italic;
    }

    .content-text a {
      color: var(--color-primary);
      text-decoration: none;
      font-weight: 500;
      transition: all 0.2s ease;
    }

    .content-text a:hover {
      color: var(--color-primary-dark);
      text-decoration: underline;
    }

    .choices-container {
      padding: var(--spacing-lg);
    }

    .choices-title {
      font-family: var(--font-secondary);
      font-size: 1.25rem;
      color: var(--color-ink);
      margin-bottom: var(--spacing-md);
      text-align: center;
    }

    .choices-list {
      list-style: none;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
    }

    .choice-item {
      width: 100%;
    }

    .choice-button {
      width: 100%;
      text-align: left;
      padding: var(--spacing-md) var(--spacing-lg);
      font-family: var(--font-primary);
      font-size: 1rem;
      transition: all 0.3s ease;
    }

    .choice-button:hover {
      transform: translateY(-2px);
    }

    .choice-button:active {
      transform: translateY(1px);
    }

    @media (max-width: 768px) {
      .content-text {
        padding: var(--spacing-lg);
      }

      .content-text h1 {
        font-size: 1.5rem;
      }

      .content-text p {
        font-size: 1rem;
      }

      .choices-container {
        padding: var(--spacing-md);
      }

      .choices-title {
        font-size: 1.1rem;
      }

      .choice-button {
        padding: var(--spacing-sm) var(--spacing-md);
      }
    }
  `);

  const contentRef = useSignal<HTMLDivElement>();

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

  return (
    <div class="story-content">
      <div 
        class="content-text"
        dangerouslySetInnerHTML={content}
      />
      <ActionDialog 
        message={actionMessage || ''} 
        onSubmit$={handleAction$}
      />
      {choices && choices.length > 0 && (
        <div class="choices-container">
          <h3 class="choices-title">Que souhaitez-vous faire ?</h3>
          <ul class="choices-list">
            {choices.map((choice, index) => (
              <li key={index} class="choice-item">
                <button class="choice-button" onClick$={choice.action}>
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
