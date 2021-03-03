import Vue from 'vue';
import CompositionPlugin from '@vue/composition-api';
import VueAnalytics from 'vue-analytics';
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
  Vue.use(VueAnalytics, {
    id: 'UA-68089198-4',
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
