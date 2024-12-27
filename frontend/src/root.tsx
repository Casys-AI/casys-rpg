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
  /**
   * The root of a QwikCity site always start with the <QwikCityProvider> component,
   * immediately followed by the document's <head> and <body>.
   *
   * Don't remove the `<head>` and `<body>` elements.
   */
  return (
    <QwikCityProvider>
      <head>
        <meta charSet="utf-8" />
        <CustomHead />
        {!isDev && <ServiceWorkerRegister />}
      </head>
      <body lang="fr" class="bg-gray-900">
        <RouterOutlet />
      </body>
    </QwikCityProvider>
  );
});
