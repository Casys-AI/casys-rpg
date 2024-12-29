import type { PageServerLoad } from './$types';
import { redirect } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ cookies }) => {
    const sessionId = cookies.get('session_id');
    const gameId = cookies.get('game_id');

    // Si on a déjà une session, rediriger vers game/read
    if (sessionId && gameId) {
        throw redirect(307, '/game/read');
    }

    return {
        hasSession: false
    };
};
