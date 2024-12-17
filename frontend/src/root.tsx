import { component$ } from '@builder.io/qwik';
import {
  QwikCityProvider,
  RouterOutlet,
  ServiceWorkerRegister,
} from '@builder.io/qwik-city';
import { CustomHead } from './components/head/CustomHead';
import { isDev } from '@builder.io/qwik/build';

import './global.css';

export default component$(() => {
  return (
    <QwikCityProvider>
      <head>
        <CustomHead />
        {!isDev && <ServiceWorkerRegister />}
      </head>
      <body lang="fr">
        <RouterOutlet />
      </body>
    </QwikCityProvider>
  );
});
