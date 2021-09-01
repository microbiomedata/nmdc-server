import Vue from 'vue';
import VueRouter from 'vue-router';

import qs from 'qs';

import V2Search from '@/views/Search/Layout.vue';
import V2SamplePage from '@/views/IndividualResults/SamplePage.vue';
import V2StudyPage from '@/views/IndividualResults/StudyPage.vue';

Vue.use(VueRouter);

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    /* V2 */
    {
      path: '/',
      name: 'V2Search',
      component: V2Search,
    },
    {
      path: '/details/sample/:id',
      name: 'V2Sample',
      component: V2SamplePage,
      props: true,
    },
    {
      path: '/details/study/:id',
      name: 'V2Study',
      component: V2StudyPage,
      props: true,
    },
    {
      path: '/v2/search',
      redirect: '/',
    },
  ],

  /* from https://github.com/vuejs/vue-router/issues/1259 */
  parseQuery(q) {
    return qs.parse(q);
  },
  stringifyQuery(q) {
    const result = qs.stringify(q);
    return result ? '?'.concat(result) : '';
  },
});
