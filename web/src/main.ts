import Vue from 'vue';
import CompositionPlugin from '@vue/composition-api';
import VueGtag from 'vue-gtag';
import { init as SentryInit } from '@sentry/vue';
import { Integrations } from '@sentry/tracing';
import { sync } from 'vuex-router-sync';
import AsyncComputed from 'vue-async-computed';

import router from '@/plugins/router';
import store from '@/plugins/store';
import { loadCurrentUser } from '@/v2/store';
import vuetify from '@/plugins/vuetify';

import App from './App.vue';

Vue.use(AsyncComputed);
Vue.use(CompositionPlugin);

/**
 * Enable instrumentation in production
 */
if (process.env.NODE_ENV === 'production') {
  const gaId = 'UA-68089198-4';
  Vue.use(VueGtag, {
    config: { id: gaId },
    includes: [{ id: gaId }],
  });
  SentryInit({
    Vue,
    dsn: 'https://87132695029c4406afe033fb3b13b115@o267860.ingest.sentry.io/5658761',
    integrations: [new Integrations.BrowserTracing()],
    tracesSampleRate: 1.0,
  });
}

Vue.config.productionTip = false;

sync(store, router);

loadCurrentUser();

new Vue({
  router,
  store,
  vuetify,
  render: (h) => h(App),
}).$mount('#app');
