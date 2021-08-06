<script lang="ts">
import {
  defineComponent, reactive, computed, toRef, PropType,
} from '@vue/composition-api';
// @ts-ignore
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import {
  Condition, entityType, EnvoNode,
} from '@/data/api';
import { unreactive, stateRefs, getTreeData } from '@/v2/store';
import useFacetSummaryData from '@/v2/use/useFacetSummaryData';
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
      required: true,
    },
  },

  setup(props, { emit }) {
    const data = reactive({
      createdDelay: false,
    });

    const conditions = toRef(props, 'conditions');
    const field = toRef(props, 'field');
    const table = toRef(props, 'table');
    const { otherConditions, myConditions } = useFacetSummaryData({ conditions, field, table });

    const tree = computed(() => stateRefs.treeData.value?.trees[`${props.field}_id`].children);
    const selected = computed(() => {
      if (stateRefs.treeData.value === null) {
        return [];
      }
      return myConditions.value.map((v) => unreactive.nodeMapLabel[v.value as string].id);
    });

    getTreeData();

    /* Enable loading bar after 2 seconds of no load, to avoid overly noisy facet dialogs */
    window.setTimeout(() => { data.createdDelay = true; }, 2000);

    async function setSelected(values: string[]) {
      // console.log(values);
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
      data, tree, selected, setSelected, normalizer,
    };
  },
});
</script>

<template>
  <div class="tree-overflow">
    <v-progress-linear
      v-if="tree === null && data.createdDelay"
      indeterminate
      style="position: absolute;"
    />
    <treeselect
      v-else-if="tree !== null"
      :value="selected"
      :options="tree"
      :max-height="8000"
      :normailzer="normalizer"
      multiple
      always-open
      class="ma-2"
      @input="setSelected"
    >
      <template #option-label="{ node }">
        <span> {{ node.label }} </span>
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

<style>
/* Hack the menu height */
/* .vue-treeselect__menu {
  height: 410px;
} */
</style>
