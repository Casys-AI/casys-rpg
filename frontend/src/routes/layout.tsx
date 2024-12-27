import { component$, Slot } from '@builder.io/qwik';
import { routeLoader$ } from '@builder.io/qwik-city';

/**
 * Logger de session pour le debug
 */
export const useSessionLogger = routeLoader$(async ({ cookie, url }) => {
  const sessionId = cookie.get('session_id')?.value;
  const gameId = cookie.get('game_id')?.value;
  
  console.log(' [Layout] Route:', url.pathname);
  console.log(' [Layout] SessionId:', sessionId);
  console.log(' [Layout] GameId:', gameId);
  
  return {
    hasSession: !!sessionId,
    hasGame: !!gameId,
    currentPath: url.pathname
  };
});

export default component$(() => {
  useSessionLogger();
  
  return (
    <div class="min-h-screen bg-white">
      <main class="container mx-auto">
        <Slot />
      </main>
    </div>
  );
});
