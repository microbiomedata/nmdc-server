import { differenceWith } from 'lodash';

import Vue from 'vue';
import Vuex from 'vuex';

import {
  api,
  /* Types */
  entityType,
  Condition,
  ResultUnion,
} from '@/data/api';

import router from './router';

Vue.use(Vuex);

interface State {
  page: number,
  pageSize: number,
  results: Record<entityType, ResultUnion>;
  route: any;
}

const store = new Vuex.Store<State>({
  state: {
    page: 1,
    pageSize: 15,
    results: {
      biosample: { count: 0, results: [] },
      study: { count: 0, results: [] },
      project: { count: 0, results: [] },
      reads_qc: { count: 0, results: [] },
      metagenome_assembly: { count: 0, results: [] },
      metagenome_annotation: { count: 0, results: [] },
      metaproteomic_analysis: { count: 0, results: [] },
      data_object: { count: 0, results: [] },
    },
    route: undefined,
  },
  getters: {
    typeResults: (state) => (type: entityType | undefined) => (
      type ? state.results[type].results : []
    ),
    type: (state): entityType | undefined => {
      const routerType = state.route.params.type;
      return routerType;
    },
    id: (state): string | undefined => state.route.params.id,
    conditions: (state): Condition[] => state.route.query.c || [],
  },
  mutations: {
    setResults(state, { type, results }: { type: entityType; results: ResultUnion }) {
      state.results[type] = results;
    },
    setPagination(state, { page, pageSize }: { page: number, pageSize: number }) {
      state.page = page;
      state.pageSize = pageSize;
    },
  },
  actions: {
    async refreshResults(
      { commit, getters, state },
      { page, pageSize }: { page?: number, pageSize?: number },
    ) {
      const newPageSize = pageSize || state.pageSize;
      const newPage = page || state.page;
      const { type, conditions }: {
        type: entityType | undefined,
        conditions: Condition[] } = getters;
      if (!type) {
        throw new Error(`Unexpected type: ${type}`);
      }
      if (newPage < 1) {
        throw new Error('Page must be > 1');
      }
      if (newPage > 1 && newPage > Math.ceil((state.results[type]?.count || 0) / newPageSize)) {
        return;
      }

      const limit = newPageSize;
      const offset = newPageSize * (newPage - 1);
      const params = { conditions, limit, offset };

      let results: ResultUnion;
      switch (type) {
        case 'study':
          results = await api.searchStudy(params);
          break;
        case 'project':
          results = await api.searchProject(params);
          break;
        case 'biosample':
          results = await api.searchBiosample(params);
          break;
        case 'metagenome_assembly':
          results = await api.searchMetagenomeAssembly(params);
          break;
        case 'metagenome_annotation':
          results = await api.searchMetagenomeAnnotation(params);
          break;
        case 'reads_qc':
          results = await api.searchReadsQC(params);
          break;
        case 'metaproteomic_analysis':
          results = await api.searchMetaproteomicAnalysis(params);
          break;
        default:
          throw new Error(`Unexpected type: ${type}`);
      }
      commit('setPagination', { page: newPage, pageSize: newPageSize });
      commit('setResults', { type, results });
    },
    async route({ getters }, { name, type, conditions }) {
      /**
       * Use the vuex route action when a route change
       * involves a change in type or conditions
       */
      if (name || type) {
        router.push({
          name,
          params: { type },
          query: { c: conditions },
        });
      } else {
        // Only change the query params to avoid double-routing
        const changed = differenceWith(getters.conditions, conditions,
          (a: Condition, b: Condition) => a.field === b.field && a.value === b.value);
        if (changed.length || conditions.length > getters.conditions.length) {
          router.push({
            query: { c: conditions },
          });
        }
      }
    },
  },
});

router.afterEach((to) => {
  if (to.name === 'Search' || to.name === 'Individual Result') {
    Vue.nextTick(() => {
      // after hook still happens before vuex sync has a chance to capture the state.
      // wait a tick before dispatch
      store.dispatch('refreshResults', { page: 1 });
    });
  }
});

export default store;
