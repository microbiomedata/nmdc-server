<script lang="ts">
import {
  defineComponent, computed, toRef, PropType,
} from '@vue/composition-api';
// @ts-ignore
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import {
  Condition, entityType, EnvoNode, FacetSummaryResponse,
} from '@/data/api';
import { unreactive, stateRefs, getTreeData } from '@/store';
import useRequest from '@/use/useRequest';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import { cloneDeep } from 'lodash';

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

  setup(props, { emit }) {
    const conditions = toRef(props, 'conditions');
    const field = toRef(props, 'field');
    const table = toRef(props, 'table');
    const { otherConditions, myConditions } = useFacetSummaryData({ conditions, field, table });

    const tree = computed(() => {
      let t = stateRefs.treeData.value?.trees[`${props.field}_id`];
      /* Eliminate nodes with only one child from the top */
      while (t && t?.length === 1 && t[0].children.length) {
        t = t[0].children;
      }
      return t;
    });
    const selected = computed(() => {
      if (stateRefs.treeData.value === null) {
        return [];
      }
      return myConditions.value.map((v) => unreactive.nodeMapLabel[v.value as string].id);
    });

    const facetSummaryMap = computed(() => {
      const resp: Record<string, number> = {};
      props.facetSummary.forEach((v) => { resp[v.facet] = v.count; });
      return resp;
    });

    const { loading, request } = useRequest();
    request(getTreeData);

    async function setSelected(values: string[]) {
      const c = cloneDeep(otherConditions.value);
      values.forEach((value) => {
        c.push({
          op: '==',
          field: field.value,
          value: unreactive.nodeMapId[value].label,
          table: table.value,
        });
      });
      emit('select', { conditions: c });
    }

    function normalizer(node: EnvoNode) {
      return {
        id: node.label,
        label: node.label,
        children: node.children,
      };
    }

    return {
      tree, selected, loading, facetSummaryMap, setSelected, normalizer,
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
      :value="selected"
      :options="tree"
      :max-height="425"
      :normailzer="normalizer"
      multiple
      always-open
      class="ma-2"
      @input="setSelected"
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
