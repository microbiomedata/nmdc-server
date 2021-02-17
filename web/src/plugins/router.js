import Vue from 'vue';
import VueRouter from 'vue-router';

import qs from 'qs';
import DatabaseSummary from '@/views/DatabaseSummary.vue';
import IndividualResults from '@/views/IndividualResults/IndividualResults.vue';
import Search from '@/views/Search/Search.vue';

import V2Search from '@/v2/views/Search/Layout.vue';
import V2SamplePage from '@/v2/views/IndividualResults/SamplePage.vue';
import V2StudyPage from '@/v2/views/IndividualResults/StudyPage.vue';

Vue.use(VueRouter);

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    /* V2 */
    {
      path: '/v2/search',
      name: 'V2Search',
      component: V2Search,
    },
    {
      path: '/v2/sample/:id',
      name: 'V2Sample',
      component: V2SamplePage,
      props: true,
    },
    {
      path: '/v2/study/:id',
      name: 'V2Study',
      component: V2StudyPage,
      props: true,
    },
    /* V1 */
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
      path: '/type/:type/search',
      name: 'Search',
      component: Search,
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
