/**
 * plugins/index.ts
 *
 * Automatically included in `./src/main.ts`
 */

import type { App } from 'vue'
import router from '../router'
import vuetify from './vuetify'
import gtag from './gtag'

export function registerPlugins (app: App) {
  app
    .use(vuetify)
    .use(router);

  if (import.meta.env.PROD) {
    app.use(gtag);
  }
}
