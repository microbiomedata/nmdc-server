import Vue from 'vue';
import VueRouter from 'vue-router';

import qs from 'qs';
import DatabaseSummary from '@/views/DatabaseSummary.vue';
import IndividualResults from '@/views/IndividualResults/IndividualResults.vue';
import Search from '@/views/Search/Search.vue';

import V2Search from '@/v2/views/Search/Layout.vue';
import V2SamplePage from '@/v2/views/IndividualResults/SamplePage.vue';

Vue.use(VueRouter);

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'Welcome',
      component: DatabaseSummary,
    },
    {
      path: '/type/:type/result',
      name: 'Individual Result',
      component: IndividualResults,
    },
    {
      path: '/type/gene_function/search',
      name: 'V2Search',
      component: V2Search,
    },
    {
      path: '/type/:type/search',
      name: 'Search',
      component: Search,
    },
    {
      path: '/v2/sample/:id',
      name: 'V2Sample',
      component: V2SamplePage,
      props: true,
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
