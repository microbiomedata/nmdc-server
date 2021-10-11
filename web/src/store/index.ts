import Vue from 'vue';
import CompositionApi, {
  computed, ComputedRef, reactive, toRefs, watchEffect,
} from '@vue/composition-api';
import { noop, uniqWith } from 'lodash';
import { removeCondition as utilsRemoveCond } from '@/data/utils';
import {
  api, Condition, DataObjectFilter, EnvoNode, EnvoTree,
} from '@/data/api';
import VueRouter from 'vue-router';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

let router: VueRouter | null = null;
const state = reactive({
  conditions: [] as Condition[],
  bulkDownloadSelected: [] as string[],
  user: null as string | null,
  hasAcceptedTerms: false,
  treeData: null as EnvoTree | null,
});
const unreactive = {
  nodeMapId: {} as Record<string, EnvoNode>,
  nodeMapLabel: {} as Record<string, EnvoNode>,
};
const queryStateKey = 'storage.queryState';

/**
 * Persist state into localstorage
 */
function persistState() {
  /* If the user is browsing anonymously, stash their state in case they log in */
  if (!state.user) {
    window.localStorage.setItem(queryStateKey, JSON.stringify({
      conditions: state.conditions,
      bulkDownloadSelected: state.bulkDownloadSelected,
    }));
  }
}

/**
 * Set conditions directly, removing duplicates
 */
function setConditions(conditions: Condition[], push = false) {
  state.conditions = uniqWith(
    conditions, (a, b) => a.field === b.field
      && a.value === b.value
      && a.op === b.op
      && a.table === b.table,
  );
  if (router) {
    // @ts-ignore
    router[push ? 'push' : 'replace']({ query: { conditions: state.conditions }, name: 'Search' }).catch(noop);
  }
}

/**
 * Restore state from localStorage and clear
 */
function restoreState() {
  const previousState = window.localStorage.getItem(queryStateKey);
  if (previousState) {
    const { conditions, bulkDownloadSelected } = JSON.parse(previousState);
    setConditions(conditions);
    state.bulkDownloadSelected = bulkDownloadSelected;
    window.localStorage.removeItem(queryStateKey);
  }
}

// @ts-ignore
window.restoreState = restoreState;

/**
 * An array of DataObjectFilter currently selected
 */
const dataObjectFilter: ComputedRef<DataObjectFilter[]> = computed(() => state
  .bulkDownloadSelected.map((val) => {
    /** See BulkDownload.vue for how this value is constructed */
    const [workflow, file_type] = val.split('::');
    return { workflow, file_type };
  }));

/**
 * load the current user on app start
 */
async function init(_router: VueRouter) {
  state.user = await api.me();
  router = _router;
  // @ts-ignore
  state.conditions = router.currentRoute.query?.conditions || [];
  if (state.user) {
    restoreState();
  } else {
    watchEffect(persistState);
  }
}

/**
 * Tree data
 */
function makeNodeMap(node: EnvoNode) {
  unreactive.nodeMapId[node.id] = node;
  unreactive.nodeMapLabel[node.label] = node;
  node.children.forEach(makeNodeMap);
}
async function getTreeData() {
  if (state.treeData === null) {
    const resp = await api.getEnvoTrees();
    state.treeData = resp;
    Object.values(resp.trees).forEach((nodeList) => nodeList.forEach(makeNodeMap));
  }
}

/**
 * For each condition, remove all others with a similar table & field.
 */
function setUniqueCondition(
  field: string[],
  table: string[],
  conditions: Condition[],
) {
  const others = state.conditions.filter((c) => (
    !field.includes(c.field)) || (!table.includes(c.table)
  ));
  setConditions([
    ...conditions,
    ...others,
  ]);
}

/**
 * For each condition, if it already exists, remove it,
 * otherwise, add it
 */
function toggleConditions(conditions: Condition[]) {
  const duplicates: Condition[] = [];
  const newConditions = conditions.filter((c) => {
    const match = state.conditions.filter((d) => (
      c.table === d.table
        && c.op === d.op
        && c.value === d.value
        && c.field === d.field));
    if (match.length === 0) {
      return true; // this is a new condition
    }
    duplicates.push(c);
    return false;
  });
  if (newConditions.length > 0 || duplicates.length > 0) {
    const withoutDuplicates = utilsRemoveCond(state.conditions, duplicates);
    setConditions([
      ...newConditions,
      ...withoutDuplicates,
    ]);
  }
}

/**
 * Remove a list of conditions
 */
function removeConditions(conditions: Condition[]) {
  if (Array.isArray(conditions)) {
    setConditions(utilsRemoveCond(state.conditions, conditions));
  } else {
    setConditions([]);
  }
}

/**
 * Note that a user has accepted the terms for the
 * current browser session
 */
function acceptTerms() {
  state.hasAcceptedTerms = true;
}

const stateRefs = toRefs(state);

export {
  stateRefs,
  dataObjectFilter,
  unreactive,
  acceptTerms,
  getTreeData,
  init,
  removeConditions,
  setUniqueCondition,
  setConditions,
  toggleConditions,
};
