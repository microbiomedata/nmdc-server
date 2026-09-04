/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */
import { createApp } from 'vue'
import * as Sentry from "@sentry/vue";
import { registerPlugins } from '@/plugins'
import router from '@/router'
import { initializeRouteState } from '@/store'
import App from './App.vue'
import 'unfonts.css'

export const app = createApp(App)

registerPlugins(app)

// Initialize Sentry if a Sentry DSN is defined.
const sentryDsn = window.__nmdc_config__?.sentryDsn;
if (typeof sentryDsn === "string" && sentryDsn.length > 0) {
  Sentry.init({
    app,
    dsn: sentryDsn,
    environment: window.__nmdc_config__?.sentryEnvironment || 'unknown',
    tracesSampleRate: window.__nmdc_config__?.sentryTracesSampleRate ?? 0.0,
    release: import.meta.env.VITE_APP_SENTRY_RELEASE_NAME || 'unknown',
  });
}

// Wait until the initial URL (including the encoded q parameter) has been parsed, then hydrate
// the store before mounting any search components. Their immediate watchers can now make their
// first requests with the correct conditions.
router.isReady().then(() => {
  initializeRouteState(router)
  app.mount('#app')
})
