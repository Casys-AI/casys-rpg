import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { v4 as uuidv4 } from 'uuid';

export const POST: RequestHandler = async ({ cookies }) => {
    console.log('Received initialize request');
    try {
        const sessionId = cookies.get('session_id') || uuidv4();
        const gameId = cookies.get('game_id') || uuidv4();

        console.log('Generated IDs:', { sessionId, gameId });

        cookies.set('session_id', sessionId, { path: '/' });
        cookies.set('game_id', gameId, { path: '/' });

        console.log('Set cookies successfully');

        return json({
            success: true,
            session_id: sessionId,
            game_id: gameId,
            message: 'Game initialized successfully'
        });
    } catch (error) {
        console.error('Error initializing game:', error);
        return json({
            success: false,
            message: error instanceof Error ? error.message : 'Failed to initialize game',
            session_id: null,
            game_id: null
        }, { status: 500 });
    }
};
