import { component$ } from '@builder.io/qwik';

interface GameControlsProps {
  showDebug: boolean;
  onToggleDebug$: () => void;
  feedbackMode: boolean;
  onToggleFeedback$: () => void;
}

export const GameControls = component$<GameControlsProps>(({
  showDebug,
  onToggleDebug$,
  feedbackMode,
  onToggleFeedback$
}) => {
  return (
    <div class="bg-white shadow-lg rounded-lg p-4">
      <h2 class="text-xl font-bold mb-4">🎮 Contrôles</h2>
      
      <div class="space-y-4">
        {/* Debug Mode */}
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">Mode Debug</span>
          <button
            onClick$={onToggleDebug$}
            class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              showDebug ? 'bg-blue-600' : 'bg-gray-200'
            }`}
          >
            <span
              class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                showDebug ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Feedback Mode */}
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">Mode Feedback</span>
          <button
            onClick$={onToggleFeedback$}
            class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              feedbackMode ? 'bg-blue-600' : 'bg-gray-200'
            }`}
          >
            <span
              class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                feedbackMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
});
