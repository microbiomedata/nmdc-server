import Vue from 'vue';
import { sync } from 'vuex-router-sync';
import AsyncComputed from 'vue-async-computed';

import router from '@/plugins/router';
import store from '@/plugins/store';
import vuetify from '@/plugins/vuetify';

import App from './App.vue';

Vue.use(AsyncComputed);

Vue.config.productionTip = false;

sync(store, router);

// Only call this once at page load
store.dispatch('load');

new Vue({
  router,
  store,
  vuetify,
  render: (h) => h(App),
}).$mount('#app');
