import { component$, useSignal, useTask$, useContextProvider, $ } from "@builder.io/qwik";
import type { DocumentHead } from "@builder.io/qwik-city";
import { marked } from "marked";
import { GameStateContext, initialGameState } from "./store";
import { CharacterSheet } from "~/components/CharacterSheet";
import { DiceRoller } from "~/components/DiceRoller";
import { FeedbackForm } from "~/components/FeedbackForm";

interface Choice {
  id: string;
  text: string;
  next_section: number;
}

export default component$(() => {
  const currentSection = useSignal('1');
  const choices = useSignal<Choice[]>([]);
  const isLoading = useSignal(false);
  const showFeedback = useSignal(false);
  const showDebug = useSignal(false);
  
  // Provide global state
  useContextProvider(GameStateContext, initialGameState);

  // Fonction pour gérer les choix
  const handleChoice$ = $((choiceId: string) => {
    const choice = choices.value.find(c => c.id === choiceId);
    if (choice) {
      currentSection.value = choice.next_section.toString();
    }
  });

  useTask$(async ({ track }) => {
    const sectionId = track(() => currentSection.value);
    if (!sectionId) return;
    
    isLoading.value = true;
    try {
      const response = await fetch(`http://localhost:8000/section/${sectionId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      currentSection.value = marked(data.content);
      choices.value = data.choices;
    } catch (error) {
      console.error('Failed to load section:', error);
    } finally {
      isLoading.value = false;
    }
  });

  return (
    <div class="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-8">
          <h1 class="text-4xl font-bold">Casys RPG</h1>
          <div class="mt-4 space-x-4">
            <button
              onClick$={() => showDebug.value = !showDebug.value}
              class={`px-4 py-2 rounded ${showDebug.value ? 'bg-blue-600' : 'bg-gray-600'} text-white`}
            >
              Mode Debug
            </button>
            <button
              onClick$={() => showFeedback.value = !showFeedback.value}
              class={`px-4 py-2 rounded ${showFeedback.value ? 'bg-blue-600' : 'bg-gray-600'} text-white`}
            >
              Feedback
            </button>
          </div>
        </header>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Character Sheet & Dice Roller */}
          <div class="md:col-span-1 space-y-4">
            <CharacterSheet />
            <DiceRoller />
          </div>

          {/* Main Content */}
          <div class="md:col-span-2 space-y-4">
            {isLoading.value ? (
              <div class="flex justify-center items-center h-64">
                <div class="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
              </div>
            ) : (
              <>
                <div 
                  class="prose dark:prose-invert max-w-none bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg"
                  dangerouslySetInnerHTML={currentSection.value} 
                />
                
                <div class="space-y-4">
                  {choices.value.map((choice) => (
                    <button
                      key={choice.id}
                      class="w-full p-4 text-left border rounded-lg bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 shadow-md"
                      onClick$={() => handleChoice$(choice.id)}
                    >
                      {choice.text}
                    </button>
                  ))}
                </div>

                {showFeedback.value && (
                  <FeedbackForm 
                    sectionId={parseInt(currentSection.value)} 
                    onSubmit$={async (feedback) => {
                      try {
                        await fetch('http://localhost:8000/feedback', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            section_id: currentSection.value,
                            feedback
                          })
                        });
                        showFeedback.value = false;
                      } catch (error) {
                        console.error('Failed to submit feedback:', error);
                      }
                    }} 
                  />
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

export const head: DocumentHead = {
  title: "Casys RPG - Interactive Game Book",
  meta: [
    {
      name: "description",
      content: "An interactive game book powered by AI",
    },
  ],
};
