<script>
import { defineComponent, computed, ref, watch } from 'vue';
import { computedAsync } from '@vueuse/core';
import Treeselect from '@zanmato/vue3-treeselect';
import '@zanmato/vue3-treeselect/dist/vue3-treeselect.min.css';
import { uniqWith } from 'lodash';
import { api } from '@/data/api';
import { makeTree } from '@/util';

export default defineComponent({
  name: 'FilterSankeyTree',
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
    hierarchy: {
      type: Array,
      default: () => [
        'ecosystem',
        'ecosystem_category',
        'ecosystem_type',
        'ecosystem_subtype',
        'specific_ecosystem',
      ],
    },
  },

  setup(props, { emit }) {
    const otherConditions = computed(() => props.conditions
      .filter((c) => (!props.hierarchy.includes(c.field)) || (c.table !== props.table)));

    const data = computedAsync(
      async () => api.getEnvironmentSankeyAggregation(otherConditions.value),
      null,
    );

    const createdDelay = ref(false);
    const filterText = ref('');
    const selected = ref([]);

    const treeData = computed(() => makeTree(data.value || [], props.hierarchy));
    
    const tree = computed(() => {
      // freeze is used because tree nodes contain back-references to their parent,
      // so recursive reactivity setup would cause a max depth exception
      return Object.freeze(treeData.value.root.children);
    });

    const myConditions = computed(() => props.conditions
      .filter((c) => (props.hierarchy.includes(c.field)) && c.table === props.table));

    /* Enable loading bar after 2 seconds of no load, to avoid overly noisy facet dialogs */
    setTimeout(() => { createdDelay.value = true; }, 2000);

    function setSelected(nodeKeys) {
      const conditions = otherConditions.value;
      nodeKeys.forEach((key) => {
        let node = treeData.value.nodeMap[key];
        do {
          conditions.push({
            op: '==',
            field: node.hierarchyKey,
            value: node.label,
            table: props.table,
          });
          node = node.parent;
        } while (node.parent);
      });
      emit('select', {
        conditions: uniqWith(conditions, (a, b) => a.field === b.field && a.value === b.value),
      });
    }

    watch(selected, (values) => {
      setSelected(values);
    }, { deep: true });

    return {
      data,
      createdDelay,
      filterText,
      selected,
      treeData,
      tree,
      otherConditions,
      myConditions,
      setSelected,
    };
  },
});
</script>

<template>
  <div class="tree-overflow">
    <v-progress-linear
      v-if="data === null && createdDelay"
      indeterminate
      style="position: absolute;"
    />
    <treeselect
      v-model="selected"
      :options="tree"
      multiple
      always-open
      class="ma-2 mt-4"
      :max-height="425"
    >
      <template #option-label="{ node }">
        <span> {{ node.label }} ({{ node.raw.count }}) </span>
      </template>
    </treeselect>
  </div>
</template>

<style lang="scss" scoped>
.tree-overflow {
  max-height: 525px;
  height: 525px;
  overflow-y: auto;
}
</style>
