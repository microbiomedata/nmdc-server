<script lang="ts">
import {
  defineComponent, computed, toRef, PropType, ref, watch,
} from 'vue';
// @ts-ignore
import Treeselect from '@zanmato/vue3-treeselect';
import '@zanmato/vue3-treeselect/dist/vue3-treeselect.min.css';

import { cloneDeep } from 'lodash';
import {
  Condition, entityType, FacetSummaryResponse,
} from '@/data/api';
import { unreactive, stateRefs, getTreeData } from '@/store';
import useRequest from '@/use/useRequest';
import useFacetSummaryData from '@/use/useFacetSummaryData';

export default defineComponent({
  components: { Treeselect },

  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String as PropType<entityType>,
      required: true,
    },
    conditions: {
      type: Array as PropType<Condition[]>,
      default: () => [],
    },
    facetSummary: {
      type: Array as PropType<FacetSummaryResponse[]>,
      default: () => [],
    },
  },
  emits: ['select'],
  setup(props, { emit }) {
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
      props.facetSummary.forEach((v) => { resp[v.facet] = v.count; });
      return resp;
    });

    const { loading, request } = useRequest();
    request(getTreeData);

    const selected = ref<string[]>([]);

    // Update selected when conditions change
    watch([myConditions, () => stateRefs.treeData.value], () => {
      if (stateRefs.treeData.value === null) {
        selected.value = [];
      } else {
        selected.value = myConditions.value.map((v) => unreactive.nodeMapLabel[v.value as string]!.id);
      }
    }, { immediate: true });

    // Update conditions when selected changes
    watch(selected, (values) => {
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

    return {
      tree, 
      selected, 
      loading, 
      facetSummaryMap, 
      setSelected, 
    };
  },
});
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
