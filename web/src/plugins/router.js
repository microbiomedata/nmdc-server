import Vue from 'vue';
import VueRouter from 'vue-router';

import qs from 'qs';
import DatabaseSummary from '@/views/DatabaseSummary.vue';
import DataObjectsList from '@/views/DataObjectsList.vue';
import IndividualResults from '@/views/IndividualResults/IndividualResults.vue';
import Search from '@/views/Search/Search.vue';

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
      path: '/type/:type/search',
      name: 'Search',
      component: Search,
    },
    {
      path: '/type/:type/data_objects/:id',
      name: 'Data Objects',
      component: DataObjectsList,
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
