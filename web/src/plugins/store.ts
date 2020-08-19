import Vue from 'vue';
import Vuex from 'vuex';

import {
  api,
  typeMap,
  /* Types */
  entityType,
  Condition,
  ResultUnion,
} from '@/data/api';

import router from './router';

Vue.use(Vuex);

interface State {
  results: Record<entityType, ResultUnion>;
  route: any;
}

function asType(type: any) {
  const t = typeMap.get(type as string);
  if (t === undefined) {
    throw new Error(`${type} is not a valid type`);
  }
  return t;
}

const store = new Vuex.Store<State>({
  state: {
    results: {
      biosample: null,
      study: null,
      project: null,
      reads_qc: null,
      metagenome_assembly: null,
      metagenome_annotation: null,
      metaproteomic_analysis: null,
      data_object: null,
    },
    route: undefined,
  },
  getters: {
    typeResults: (state) => (type: string | undefined) => {
      if (type && state.results[asType(type)] !== null) {
        return state.results[asType(type)]?.results;
      }
      return undefined;
    },
    type: (state): entityType | undefined => {
      const routerType = state.route.params.type;
      return routerType ? asType(routerType) : undefined;
    },
    id: (state): string | undefined => state.route.params.id,
    conditions: (state): Condition[] => state.route.query.c || [],
  },
  mutations: {
    setResults(state, { type, results }: { type: entityType; results: ResultUnion }) {
      state.results[type] = results;
    },
  },
  actions: {
    async refreshResults({ commit, getters }) {
      console.log('refresh');
      const { conditions, type } = getters;
      const params = { conditions };
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
      commit('setResults', { type, results });
    },
    async refreshAll({ dispatch }) {
      await dispatch('refreshResults');
    },
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async route({ state }, { name, type, conditions }) {
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
        router.push({
          query: { c: conditions },
        });
      }
    },
  },
});

router.afterEach((to) => {
  if (to.name === 'Search' || to.name === 'Individual Result') {
    Vue.nextTick(() => {
      // after hook still happens before vuex sync has a chance to capture the state.
      // wait a tick before dispatch
      store.dispatch('refreshAll');
    });
  }
});

export default store;
