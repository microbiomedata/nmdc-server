import Vue from 'vue';
import VueRouter from 'vue-router';
import AsyncComputed from 'vue-async-computed';

import routes from './routes';
import App from './App.vue';
import vuetify from './plugins/vuetify';

Vue.use(VueRouter);
Vue.use(AsyncComputed);

Vue.config.productionTip = false;

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
});

new Vue({
  router,
  vuetify,
  render: (h) => h(App),
}).$mount('#app');
