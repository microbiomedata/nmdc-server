<script lang="ts">
import { defineComponent, reactive, computed } from '@vue/composition-api';
// @ts-ignore
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { api, EnvoNode, EnvoTree } from '@/data/api';
import FacetSummary from '@/mixins/FacetSummary';

export default defineComponent({
  mixins: [FacetSummary],

  components: { Treeselect },

  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String,
      required: true,
    },
    conditions: {
      type: Array,
      required: true,
    },
  },

  setup(props) {
    const data = reactive({
      createdDelay: false,
      treeData: null as EnvoTree | null,
      value: [] as EnvoNode[],
    });

    const getTreeData = async () => {
      data.treeData = await api.getEnvoTrees();
    };
    getTreeData();

    const tree = computed(() => data.treeData?.trees[`${props.field}_id`].children);

    window.setTimeout(() => { data.createdDelay = true; }, 2000);

    async function setSelected(nodes: EnvoNode[]) {
      data.value = nodes;
      // const conditions = root.otherConditions;
      // nodeKeys.forEach((key) => {
      //   let node = this.treeData.nodeMap[key];
      //   do {
      //     conditions.push({
      //       op: '==',
      //       field: node.heirarchyKey,
      //       value: node.label,
      //       table: props.table,
      //     });
      //     node = node.parent;
      //   } while (node.parent);
      // });
      // emit('select', {
      //   conditions: uniqWith(conditions, (a, b) => a.field === b.field && a.value === b.value),
      // });
    }

    return { data, tree, setSelected };
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
      :value="data.value"
      :options="tree"
      :max-height="410"
      value-format="object"
      multiple
      always-open
      class="ma-2 mt-4"
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
.vue-treeselect__menu {
  height: 410px;
}
</style>
