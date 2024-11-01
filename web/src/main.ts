import Vue from 'vue';
import CompositionPlugin from '@vue/composition-api';
import VueGtag from 'vue-gtag';
import { init as SentryInit } from '@sentry/vue';
import AsyncComputed from 'vue-async-computed';

import router from '@/plugins/router';
import vuetify from '@/plugins/vuetify';
import { provideRouter } from '@/use/useRouter';

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
