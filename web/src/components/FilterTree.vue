<script setup lang="ts">
import { computed, toRef, ref, watch, nextTick } from 'vue';
// @ts-ignore
import Treeselect from '@zanmato/vue3-treeselect';
import '@zanmato/vue3-treeselect/dist/vue3-treeselect.min.css';

import { cloneDeep } from 'lodash';
import {
  Condition, EntityType, FacetSummaryResponse,
} from '@/data/api';
import { unreactive, stateRefs, getTreeData } from '@/store';
import useRequest from '@/use/useRequest';
import useFacetSummaryData from '@/use/useFacetSummaryData';

const props = withDefaults(defineProps<{
  field: string;
  table: EntityType;
  conditions?: Condition[];
  facetSummary?: FacetSummaryResponse[] | null;
}>(), {
  conditions: () => [],
  facetSummary: null,
});

const emit = defineEmits<{
  (e: 'select', value: { conditions: Condition[] }): void;
}>();

const conditions = toRef(props, 'conditions');
const field = toRef(props, 'field');
const table = toRef(props, 'table');
const { otherConditions, myConditions } = useFacetSummaryData({ conditions, field, table });

const tree = computed(() => {
  let t = stateRefs.treeData.value?.trees[`${props.field}_id`];
  /* Eliminate nodes with only one child from the top */
  while (t && t?.length === 1 && t[0]?.children?.length) {
    t = t[0].children;
  }
  return t;
});

const facetSummaryMap = computed(() => {
  const resp: Record<string, number> = {};
  props.facetSummary?.forEach((v) => { resp[v.facet] = v.count; });
  return resp;
});

const { loading, request } = useRequest();
request(getTreeData);

const selected = ref<string[]>([]);
let suppressEmit = false;

// Sync the treeselect's internal `selected` state to match the incoming conditions prop.
// Setting `suppressEmit = true` prevents the watcher below from treating this programmatic
// update as a user selection and emitting a spurious `select` event back to the parent.
// `await nextTick()` defers the flag reset until after Vue has flushed the queued watcher
// on `selected`, ensuring the guard is still active when that watcher runs.
watch([myConditions, () => stateRefs.treeData.value], async () => {
  suppressEmit = true;
  if (stateRefs.treeData.value === null) {
    selected.value = [];
  } else {
    selected.value = myConditions.value.map((v) => unreactive.nodeMapLabel[v.value as string]!.id);
  }
  await nextTick();
  suppressEmit = false;
}, { immediate: true });

// Propagate user-driven selection changes to the parent as a new conditions list.
// Skipped when `suppressEmit` is true (i.e. the change came from the watcher above,
// not from the user interacting with the treeselect).
watch(selected, (values) => {
  if (suppressEmit) return;
  setSelected(values);
}, { deep: true });

function setSelected(values: string[]) {
  const c = cloneDeep(otherConditions.value);
  values.forEach((value) => {
    c.push({
      op: '==',
      field: field.value,
      value: unreactive.nodeMapId[value]!.label,
      table: table.value,
    });
  });
  emit('select', { conditions: c });
}
</script>

<template>
  <div class="tree-overflow">
    <v-progress-linear
      v-if="loading"
      indeterminate
      style="position: absolute;"
    />
    <treeselect
      v-else-if="tree !== null"
      v-model="selected"
      :options="tree"
      multiple
      always-open
      :match-keys="['label', 'id']"
      placeholder="Select or search by ID or label"
      class="ma-2"
    >
      <template #option-label="{ node }">
        <span> {{ node.label }} ({{ facetSummaryMap[node.label] || '0' }}) </span>
      </template>
    </treeselect>
  </div>
</template>

<style lang="scss" scoped>
.tree-overflow {
  max-height: 475px;
  height: 475px;
  overflow-y: auto;
}
</style>
