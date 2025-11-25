/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */
import { createApp } from 'vue'
import * as Sentry from "@sentry/vue";
import { registerPlugins } from '@/plugins'
import App from './App.vue'
import 'unfonts.css'

export const app = createApp(App)

registerPlugins(app)

if (import.meta.env.PROD) {
  Sentry.init({
    app,
    dsn: 'https://87132695029c4406afe033fb3b13b115@o267860.ingest.sentry.io/5658761',
    tracesSampleRate: 1.0,
  });
}

app.mount('#app')
