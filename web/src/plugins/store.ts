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
  loading: boolean;
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
    loading: false,
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
    type: (state): entityType => {
      const routerType = state.route.params.type;
      return routerType ? asType(routerType) : undefined;
    },
    conditions: (state): Condition[] => state.route.query.conditions || [],
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
    setLoading(state, loading) {
      state.loading = loading;
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
    async refreshFacetSummaries({ commit, state, getters }) {
      const { dbsummary } = state;
      if (dbsummary) {
        const type = asType(getters.type);
        const { conditions } = getters;
        Object.keys(dbsummary[type].attributes).forEach(async (field) => {
          const summary = await api.getFacetSummary(type, field, conditions);
          commit('setFacetSummary', { type, field, summary });
        });
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
    async refreshAll({ dispatch, state, commit }) {
      if (!state.loading) {
        commit('setLoading', true);
        await Promise.all([
          dispatch('refreshResults'),
          dispatch('refreshFacetSummaries'),
        ]).finally(() => {
          commit('setLoading', false);
        });
      }
    },
    async load({ dispatch }) {
      /* TODO: Load type and conditions from router */
      await Promise.all([
        dispatch('fetchAllSamples'),
        dispatch('fetchDBSummary'),
      ]);
    },
  },
});
