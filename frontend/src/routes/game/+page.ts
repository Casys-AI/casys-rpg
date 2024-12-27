import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ data }) => {
    if (data.hasSession) {
        throw redirect(307, '/game/read');
    }
    return data;
};
