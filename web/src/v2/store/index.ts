import Vue from 'vue';
import CompositionApi, { reactive, toRefs } from '@vue/composition-api';
import { uniqWith } from 'lodash';

import { removeCondition as utilsRemoveCond } from '@/data/utils';
import { api, Condition } from '@/data/api';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

const state = reactive({
  conditions: [] as Condition[],
  user: null as string | null,
});
const stateRefs = toRefs(state);

/**
 * load the current user on app start
 */
async function loadCurrentUser() {
  state.user = await api.me();
}

/*
 * Set conditions directly, removing duplicates
 */
function setConditions(conditions: Condition[]) {
  state.conditions = uniqWith(
    conditions, (a, b) => a.field === b.field
      && a.value === b.value
      && a.op === b.op
      && a.table === b.table,
  );
}

/**
 * For each condition, remove all others with a similar table & field.
 */
function setUniqueCondition(
  field: string,
  table: string,
  conditions: Condition[],
) {
  const others = state.conditions.filter((c) => (c.field !== field) || (c.table !== table));
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
    state.conditions = utilsRemoveCond(state.conditions, conditions);
  } else {
    state.conditions = [];
  }
}

export {
  stateRefs,
  loadCurrentUser,
  removeConditions,
  setUniqueCondition,
  setConditions,
  toggleConditions,
};
