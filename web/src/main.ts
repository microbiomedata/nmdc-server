import Vue from 'vue';
import CompositionPlugin from '@vue/composition-api';
import { sync } from 'vuex-router-sync';
import AsyncComputed from 'vue-async-computed';

import router from '@/plugins/router';
import store from '@/plugins/store';
import { loadCurrentUser } from '@/v2/store';
import vuetify from '@/plugins/vuetify';

import App from './App.vue';

Vue.use(AsyncComputed);
Vue.use(CompositionPlugin);

Vue.config.productionTip = false;

sync(store, router);

loadCurrentUser();

new Vue({
  router,
  store,
  vuetify,
  render: (h) => h(App),
}).$mount('#app');
