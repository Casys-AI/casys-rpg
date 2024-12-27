import type { PageServerLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import type { Actions } from '@sveltejs/kit';
import { v4 as uuidv4 } from 'uuid';

export const load: PageServerLoad = async ({ cookies }) => {
    const sessionId = cookies.get('session_id');
    const gameId = cookies.get('game_id');

    return {
        hasSession: !!sessionId && !!gameId
    };
};

export const actions = {
    init: async ({ cookies }) => {
        const sessionId = uuidv4();
        const gameId = uuidv4();

        cookies.set('session_id', sessionId, { path: '/' });
        cookies.set('game_id', gameId, { path: '/' });

        throw redirect(303, '/game/read');
    }
} satisfies Actions;
