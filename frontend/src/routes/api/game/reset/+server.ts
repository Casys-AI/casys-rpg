import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ cookies }) => {
    // Effacer les cookies
    cookies.delete('session_id', { path: '/' });
    cookies.delete('game_id', { path: '/' });

    return json({ success: true });
};
