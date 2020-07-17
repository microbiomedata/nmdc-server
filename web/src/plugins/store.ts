import Vue from 'vue';
import Vuex from 'vuex';

import {
  api,
  typeMap,
  /* Types */
  entityType,
  Condition,
  DatabaseSummaryResponse,
  BiosampleSearchResult,
  SearchResponse,
  FacetSummaryResponse,
  ResultUnion,
} from '@/data/api';

import router from './router';

Vue.use(Vuex);

type Results = Record<entityType, ResultUnion>;
type FacetSummaryResponseMap = Record<string, FacetSummaryResponse[]>;

/* TODO: use router for type and conditions, and make them into getters */
interface State {
  allSamples?: SearchResponse<BiosampleSearchResult>;
  dbsummary?: DatabaseSummaryResponse;
  facetSummaries: {
    biosample: FacetSummaryResponseMap;
    study: FacetSummaryResponseMap;
    project: FacetSummaryResponseMap;
    data_object: FacetSummaryResponseMap;
  };
  results: Results;
  route: any;
  loading: Record<string, boolean>;
}

function asType(type: any) {
  const t = typeMap.get(type as string);
  if (t === undefined) {
    throw new Error(`${type} is not a valid type`);
  }
  return t;
}

export default new Vuex.Store<State>({
  state: {
    allSamples: undefined,
    dbsummary: undefined,
    facetSummaries: {
      biosample: {},
      study: {},
      project: {},
      data_object: {},
    },
    results: {
      biosample: null,
      study: null,
      project: null,
      data_object: null,
    },
    route: undefined,
    loading: {},
  },
  getters: {
    primitiveFields: (state) => (type: string) => {
      if (state.dbsummary) {
        return Object.keys(state.dbsummary[asType(type)].attributes);
      }
      return [];
    },
    count: (state) => (type: string) => {
      if (state.dbsummary) {
        return state.dbsummary[asType(type)].total;
      }
      return 0;
    },
    typeResults: (state) => (type: string) => {
      if (state.results[asType(type)] !== null) {
        return state.results[asType(type)]?.results;
      }
      return undefined;
    },
    type: (state): entityType | undefined => {
      const routerType = state.route.params.type;
      return routerType ? asType(routerType) : undefined;
    },
    conditions: (state): Condition[] => state.route.query.c || [],
  },
  mutations: {
    setDBSummary(state, resp: DatabaseSummaryResponse) {
      state.dbsummary = resp;
    },
    setAllSamples(state, results: SearchResponse<BiosampleSearchResult>) {
      state.allSamples = results;
    },
    setResults(state, { type, results }: { type: entityType; results: ResultUnion }) {
      state.results[type] = results;
    },
    setFacetSummary(state, { type, field, summary }: {
      type: entityType; field: string; summary: FacetSummaryResponse[];
    }) {
      Vue.set(state.facetSummaries[type], field, summary);
    },
    resetFacetSummaries(state, type) {
      Vue.set(state.facetSummaries, type, {});
    },
    setLoading(state, { name, loading }) {
      Vue.set(state.loading, name, loading);
    },
  },
  actions: {
    async fetchAllSamples({ commit, state }) {
      if (state.allSamples === undefined) {
        const results = await api.searchBiosample({ conditions: [] });
        commit('setAllSamples', results);
      }
    },
    async fetchDBSummary({ commit, state }) {
      if (state.dbsummary === undefined) {
        const summary = await api.getDatabaseSummary();
        commit('setDBSummary', summary);
      }
    },
    async fetchFacetSummary({ commit, state, getters }, { field, conditions }) {
      /* Fetch facet summaries for a given field, and cache it */
      const type = asType(getters.type);
      const existing = state.facetSummaries[type][field];
      if (existing) {
        return;
      }
      const loadingname = `${field}-summary`;
      if (!state.loading[loadingname]) {
        commit('setLoading', { name: loadingname, loading: true });
        try {
          const summary = await api.getFacetSummary(type, field, conditions);
          commit('setFacetSummary', { type, field, summary });
        } finally {
          commit('setLoading', { name: loadingname, loading: false });
        }
      }
    },
    async refreshResults({ commit, getters }) {
      const { conditions } = getters;
      const params = { conditions };
      let results: ResultUnion;
      const type = asType(getters.type);
      switch (type) {
        case 'study':
          results = await api.searchStudy(params);
          break;
        case 'project':
          results = await api.searchProject(params);
          break;
        case 'data_object':
          results = await api.searchBiosample(params);
          break;
        case 'biosample':
          results = await api.searchBiosample(params);
          break;
        default:
          throw new Error(`Unexpected type: ${type}`);
      }
      commit('setResults', { type, results });
    },
    async refreshAll({
      dispatch, state, commit, getters,
    }) {
      if (!state.loading.all) {
        commit('setLoading', { name: 'all', loading: true });
        try {
          await dispatch('refreshResults');
        } finally {
          commit('resetFacetSummaries', getters.type);
          commit('setLoading', { name: 'all', loading: false });
        }
      }
    },
    async load({ dispatch }) {
      await Promise.all([
        dispatch('fetchAllSamples'),
        dispatch('fetchDBSummary'),
      ]);
    },
    async route({ dispatch, state }, { name, type, conditions }) {
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
      dispatch('refreshAll');
    },
  },
});
