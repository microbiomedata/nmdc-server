import Vue from 'vue';
import VueGtag from 'vue-gtag';
import { init as SentryInit } from '@sentry/vue';
import AsyncComputed from 'vue-async-computed';

import router from '@/plugins/router';
import vuetify from '@/plugins/vuetify';
import { provideRouter } from '@/use/useRouter';

import App from './App.vue';

Vue.use(AsyncComputed);

/**
 * Enable instrumentation in production
 */
if (process.env.NODE_ENV === 'production') {
  const gaId = process.env.VUE_APP_NMDC_GOOGLE_ANALYTICS_ID;
  Vue.use(VueGtag, {
    config: { id: gaId },
    includes: [{ id: gaId }],
  }, router);
  SentryInit({
    Vue,
    dsn: 'https://87132695029c4406afe033fb3b13b115@o267860.ingest.sentry.io/5658761',
    tracesSampleRate: 1.0,
  });
}

Vue.config.productionTip = false;

new Vue({
  router,
  vuetify,
  setup() {
    provideRouter(router);
  },
  render: (h) => h(App),
}).$mount('#app');
