<script lang="ts">
import {
  defineComponent, computed, toRef, PropType, ref, watch,
} from 'vue';
// @ts-ignore
import Treeselect from '@zanmato/vue3-treeselect';
import '@zanmato/vue3-treeselect/dist/vue3-treeselect.min.css';

import { cloneDeep } from 'lodash';
import {
  Condition, entityType, EnvoNode, FacetSummaryResponse,
} from '@/data/api';
import { unreactive, stateRefs, getTreeData } from '@/store';
import useRequest from '@/use/useRequest';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import { LoadOptionsParams } from '@/types';

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

    function normalizer(node: EnvoNode) {
      return {
        id: node.label,
        label: node.label,
        children: node.children,
        isDefaultExpanded: node.isDefaultExpanded || node.isExpanded || false,
      };
    }

    /**
     * Recursively search through an EnvoNode tree by label and id.
     * @param nodes - Array of EnvoNode to search through
     * @param query - Search term (case-insensitive)
     * @param ancestors - Array of ancestor nodes (used for tracking during recursion)
     * @returns Array of nodes that match the query or have matching descendants, including their ancestors
     */
    function searchTree(nodes: EnvoNode[], query: string, ancestors: EnvoNode[] = []): EnvoNode[] {
      if (!query || query.trim() === '') {
        return nodes;
      }

      const lowerQuery = query.toLowerCase();
      const results: EnvoNode[] = [];

      for (const node of nodes) {
        const matchesLabel = node.label.toLowerCase().includes(lowerQuery);
        const matchesId = node.id.toLowerCase().includes(lowerQuery);
        const isMatch = matchesLabel || matchesId;

        let childResults: EnvoNode[] = [];
        if (node.children && node.children.length > 0) {
          childResults = searchTree(node.children, query, [...ancestors, node]);
        }

        if (isMatch || childResults.length > 0) {
          // Return normalized node structure that Treeselect expects
          const matchedNode = {
            id: node.label,
            label: node.label,
            children: childResults.length > 0 ? childResults : node.children?.map(normalizer),
            isDefaultExpanded: childResults.length > 0 ? true : false,
          };
          results.push(matchedNode);
        }
      }

      return results;
    }

    /**
     * Programmatically load the options for the Treeselect component.
     * This allows us to override the default search behavior.
     */
    function loadOptions({ action, callback, searchQuery }: LoadOptionsParams) {
      if (action === "ASYNC_SEARCH") {
        if (searchQuery && searchQuery.trim() !== '') {
          const searchResults = searchTree(tree.value || [], searchQuery);
          callback(null, searchResults);
        } else {
          callback(null, tree.value || []);
        }
      } else if (action === "LOAD_ROOT_OPTIONS") {
        callback(null, tree.value || []);
      }
    }

    return {
      tree, 
      selected, 
      loading, 
      facetSummaryMap, 
      setSelected, 
      normalizer,
      loadOptions,
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
      :normailzer="normalizer"
      multiple
      always-open
      async
      :load-options="loadOptions"
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
