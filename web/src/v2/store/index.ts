import Vue from 'vue';
import CompositionApi, { reactive, toRef } from '@vue/composition-api';

import utilsRemoveCond from '@/data/utils';
import { Condition } from '@/data/api';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

const state = reactive({
  conditions: [] as Condition[],
});

function addConditions(conditions: Condition[]) {
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
    state.conditions = [
      ...newConditions,
      ...utilsRemoveCond(state.conditions, duplicates),
    ];
  }
}

function removeConditions(conditions: Condition[]) {
  state.conditions = utilsRemoveCond(state.conditions, conditions);
}

if (process.env.NODE_ENV !== 'production') {
  // @ts-ignore
  window.appstate = state;
}

const conditions = toRef(state, 'conditions');

export {
  conditions,
  addConditions,
  removeConditions,
};
