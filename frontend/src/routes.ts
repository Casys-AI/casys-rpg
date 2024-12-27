import type { RouteLoader } from '@builder.io/qwik-city';

export const routes: RouteLoader[] = [
  {
    path: '/',
    component: () => import('./routes/index'),
  },
  {
    path: '/game',
    component: () => import('./routes/game/index'),
  },
  {
    path: '/game/read',
    component: () => import('./routes/game/read/index'),
  },
];
