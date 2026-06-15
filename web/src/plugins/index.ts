/**
 * plugins/index.ts
 *
 * Automatically included in `./src/main.ts`
 */

import type { App } from 'vue'
import pinia from './pinia'
import router from '../router'
import vuetify from './vuetify'
import gtag from './gtag'

export function registerPlugins (app: App) {
  app
    .use(vuetify)
    .use(pinia)
    .use(router);

  if (import.meta.env.PROD) {
    app.use(gtag);
  }
}
