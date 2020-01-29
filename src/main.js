import Vue from 'vue';
import VueRouter from 'vue-router';
import App from './App.vue';
import vuetify from './plugins/vuetify';

Vue.use(VueRouter);

Vue.config.productionTip = false;

const routes = [];
const router = new VueRouter({
  mode: 'history',
  routes,
});

new Vue({
  router,
  vuetify,
  render: (h) => h(App),
}).$mount('#app');
