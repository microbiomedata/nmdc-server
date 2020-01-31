import Vue from 'vue';
import VueRouter from 'vue-router';

import routes from './routes';
import App from './App.vue';
import vuetify from './plugins/vuetify';

Vue.use(VueRouter);

Vue.config.productionTip = false;

// eslint-disable-next-line no-console
console.log(process.env);

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
