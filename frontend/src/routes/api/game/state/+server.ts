import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ cookies }) => {
    try {
        const sessionId = cookies.get('session_id');
        const gameId = cookies.get('game_id');
        
        if (!sessionId || !gameId) {
            return json({
                success: false,
                message: 'No session found'
            }, { status: 401 });
        }

        // Exemple de state pour le développement
        return json({
            success: true,
            game_id: gameId,
            state: {
                session_id: sessionId,
                game_id: gameId,
                narrative: {
                    section_number: 1,
                    content: "Vous vous enfoncez confortablement dans le siège antigravitationnel, face aux commandes de votre vaisseau spatial. Après avoir vérifié le système de sécurité, vous examinez attentivement le tableau de bord. Il ne présente aucune complexité : une simple console d'ordinateur reliée à un terminal de liaison et quelques écrans.\n\nLe circuit micro-électronique du système alpha ziridium est profondément enfoui dans les entrailles du vaisseau, et vous n'aurez jamais à vous en préoccuper le moins du monde. Si une panne quelconque venait à se déclarer, ou s'il se produisait le moindre incident, votre ingénieur robot interviendrait sur-le-champ.\n\nLa préprogrammation de votre voyage a été établie pour vous mener en premier lieu sur Tropos. Vous entamez les procédures de départ : interrogation de l'ordinateur concernant tous les points vitaux du vaisseau. Une voix impersonnelle se fait entendre aussitôt : « Vérifications effectuées. Fonctionnement optimal. »\n\nPuis vous passez à la deuxième opération : contact avec la tour de contrôle. Paré au décollage ! Vous appuyez sur un bouton... et c'est le grand voyage. Au bout de quelques minutes, les malaises dus à l'accélération s'estompent : vous quittez l'exosphère terrienne et pénétrez dans la nuit spatiale, aussi noire que de l'encre.\n\nLe générateur gravitationnel est automatiquement enclenché de sorte que la pesanteur normale est maintenue dans votre vaisseau, ce qui vous permet, ainsi qu'à vos robots, de vous déplacer librement. Vous allumez l'écran de vision rétrospective pour observer une dernière fois la Terre qui rétrécit et s'éloigne, des bancs de nuages glissent paresseusement et le soleil se réfléchit sur les glaces polaires du cercle arctique.\n\nBien que l'occasion vous ait été donnée à maintes reprises de contempler ce spectacle au cours de vos voyages vers Vénus ou vers Mercure, vous ressentez toujours, à sa vue, un petit pincement au cœur et une émotion nostalgique. Reverrez-vous jamais la Terre ? D'un haussement d'épaules, vous chassez ces pensées car seul, compte, désormais, votre mission.\n\nDes heures s'écoulent, uniformes et lentes. Puis votre écran revient soudain à la vie. L'ordinateur de bord vous avertit qu'un autre vaisseau spatial suit la même trajectoire que vous tout en maintenant soigneusement un écart constant. Cela ressemble à s'y méprendre à une filature.\n\nAllez-vous donner l'ordre à votre ordinateur d'engager la procédure d'évasion (rendez-vous au [[48]]) ou préférez-vous continuer votre route (rendez-vous au [[398]]) ?",
                    source_type: "raw",
                    error: null,
                    timestamp: new Date().toISOString(),
                    last_update: new Date().toISOString()
                },
                rules: {
                    section_number: 1,
                    dice_type: "none",
                    needs_dice: false,
                    needs_user_response: true,
                    next_action: "user_first",
                    conditions: [],
                    choices: [
                        {
                            text: "Engager la procédure d'évasion",
                            type: "direct",
                            target_section: 48,
                            conditions: [],
                            dice_type: "none",
                            dice_results: {}
                        },
                        {
                            text: "Continuer votre route",
                            type: "direct",
                            target_section: 398,
                            conditions: [],
                            dice_type: "none",
                            dice_results: {}
                        }
                    ],
                    rules_summary: "Le joueur doit choisir entre engager la procédure d'évasion ou continuer sa route.",
                    error: null,
                    source: "llm_analysis",
                    source_type: "processed",
                    last_update: new Date().toISOString()
                },
                trace: null,
                character: null,
                decision: null,
                error: null,
                section_number: 1,
                player_input: null,
                content: null
            }
        });
    } catch (error) {
        console.error('Error getting game state:', error);
        return json({
            success: false,
            message: error instanceof Error ? error.message : 'Failed to get game state'
        }, { status: 500 });
    }
};
