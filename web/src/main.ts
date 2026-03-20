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
  const sentryDsn = window.__nmdc_config__?.sentryDsn;
  if (sentryDsn) {
    Sentry.init({
      app,
      dsn: sentryDsn,
      environment: window.__nmdc_config__?.sentryEnvironmentName || 'unknown',
      tracesSampleRate: 1.0,
      release: import.meta.env.VITE_APP_SENTRY_RELEASE_NAME || 'unknown',
    });
  }
}

app.mount('#app')
