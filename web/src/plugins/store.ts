import Vue from 'vue';
import Vuex from 'vuex';

import {
  api,
  typeMap,
  /* Types */
  entityType,
  Condition,
  DatabaseSummaryResponse,
  DatabaseStatsResponse,
  BiosampleSearchResult,
  SearchResponse,
  FacetSummaryResponse,
  ResultUnion,
} from '@/data/api';

import router from './router';

Vue.use(Vuex);

type FacetSummaryResponseMap = Record<string, FacetSummaryResponse[]>;

interface State {
  allSamples?: SearchResponse<BiosampleSearchResult>;
  dbsummary?: DatabaseSummaryResponse;
  dbstats?: DatabaseStatsResponse;
  facetSummaries: Record<entityType, FacetSummaryResponseMap>;
  facetSummariesUnconditional: Record<entityType, FacetSummaryResponseMap>;
  results: Record<entityType, ResultUnion>;
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

const store = new Vuex.Store<State>({
  state: {
    allSamples: undefined,
    dbsummary: undefined,
    dbstats: undefined,
    facetSummaries: {
      biosample: {},
      study: {},
      project: {},
      reads_qc: {},
      metagenome_assembly: {},
      metagenome_annotation: {},
      metaproteomic_analysis: {},
      data_object: {},
    },
    facetSummariesUnconditional: {
      biosample: {},
      study: {},
      project: {},
      reads_qc: {},
      metagenome_assembly: {},
      metagenome_annotation: {},
      metaproteomic_analysis: {},
      data_object: {},
    },
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
    loading: {},
  },
  getters: {
    primitiveFields: (state, getters) => (type: string | undefined) => (
      Object.keys(getters.typeSummary(type))
    ),
    typeSummary: (state) => (type: string | undefined) => {
      if (type && state.dbsummary) {
        return state.dbsummary[asType(type)].attributes;
      }
      return {};
    },
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
    setDBSummary(state, resp: DatabaseSummaryResponse) {
      state.dbsummary = resp;
    },
    setDBStats(state, resp: DatabaseStatsResponse) {
      state.dbstats = resp;
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
    setFacetSummaryUnconditional(state, { type, field, summary }: {
      type: entityType; field: string; summary: FacetSummaryResponse[];
    }) {
      Vue.set(state.facetSummariesUnconditional[type], field, summary);
    },
    resetFacetSummaries(state, type) {
      Vue.set(state.facetSummaries, type, {});
      Vue.set(state.facetSummariesUnconditional, type, {});
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
    async fetchDBStats({ commit, state }) {
      if (state.dbstats === undefined) {
        const stats = await api.getDatabaseStats();
        commit('setDBStats', stats);
      }
    },
    async fetchFacetSummary({ commit, state }, { field, conditions, type: t }) {
      /* Fetch facet summaries for a given field, and cache it */
      const type = asType(t);
      const existing = state.facetSummaries[type][field];
      if (existing) {
        return;
      }
      const loadingname = `${field}-summary`;
      if (!state.loading[loadingname]) {
        commit('setLoading', { name: loadingname, loading: true });
        try {
          // Check if we need to fetch unconditional facets
          let existingUnconditional = state.facetSummariesUnconditional[type][field];
          if (!existingUnconditional) {
            existingUnconditional = await api.getFacetSummary(type, field, []);
            commit('setFacetSummaryUnconditional',
              { type, field, summary: existingUnconditional });
          }
          if (conditions.length > 0) {
            const summary = await api.getFacetSummary(type, field, conditions);
            commit('setFacetSummary', { type, field, summary });
          } else {
            commit('setFacetSummary', { type, field, summary: existingUnconditional });
          }
        } finally {
          commit('setLoading', { name: loadingname, loading: false });
        }
      }
    },
    async refreshResults({ commit, getters }) {
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
