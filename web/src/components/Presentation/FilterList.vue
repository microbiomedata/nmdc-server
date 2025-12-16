<script lang="ts">
import {
  defineComponent, computed, ref, toRef, watch, onMounted, nextTick, PropType,
} from 'vue';
// @ts-ignore
import { valueDisplayName, fieldDisplayName } from '@/util';
import { api, Condition, entityType, FacetSummaryResponse } from '@/data/api';
import useFacetSummaryData from '@/use/useFacetSummaryData';

export interface FacetItem extends FacetSummaryResponse {
  isSelectable: boolean;
  name: string;
}

export default defineComponent({
  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String as PropType<entityType>,
      required: true,
    },
    useAllConditions: {
      type: Boolean,
      default: false,
    },
    conditions: {
      type: Array as PropType<Condition[]>,
      default: () => [],
    },
  },
  emits: ['select'],
  setup(props, { emit }) {
    const filterText = ref('');
    const createdDelay = ref(false);
    const facetSummary = ref<FacetSummaryResponse[]>([]);
    const facetSummaryUnconditional = ref<FacetSummaryResponse[]>([]);
    const selectedItems = ref<FacetItem[]>([]);
    const isUpdatingFromConditions = ref(false);
    
    const tableHeaders = ref([
      {
        title: 'Facet',
        key: 'name',
        width: '300',
        sortable: true,
      },
      {
        title: 'Count',
        key: 'count',
        sortable: true,
        width: 90,
      },
    ]);

    const field = toRef(props, 'field');
    const table = toRef(props, 'table');
    const conditions = toRef(props, 'conditions');
    
    const { otherConditions, myConditions } = useFacetSummaryData({ field, table, conditions });

    const facetSummaryAggregate = computed<FacetItem[]>(() => facetSummary.value
      .map((item) => ({
        ...item,
        isSelectable: true,
        name: valueDisplayName(props.field, item.facet),
      }))
      .concat(facetSummaryUnconditional.value
        .filter((item1) => !facetSummary.value.some((item2) => item1.facet === item2.facet))
        .map((item) => ({
          ...item,
          isSelectable: false,
          name: valueDisplayName(props.field, item.facet),
        }))));

    async function fetchFacetSummary() {
      try {
        const conds = otherConditions.value.concat(props.useAllConditions ? myConditions.value : []);
        facetSummary.value = await api.getFacetSummary(
          props.table,
          props.field,
          conds,
        );
      } catch (_error) {
        facetSummary.value = [];
      }
    }

    async function fetchFacetSummaryUnconditional() {
      try {
        facetSummaryUnconditional.value = await api.getFacetSummary(
          props.table,
          props.field,
          [],
        );
      } catch (_error) {
        facetSummaryUnconditional.value = [];
      }
    }

    // Watch for changes in conditions and refetch data
    watch(otherConditions, () => {
      fetchFacetSummary();
    }, { deep: true, immediate: true });

    watch(myConditions, () => {
      fetchFacetSummary();
    }, { deep: true });

    watch(() => props.useAllConditions, () => {
      fetchFacetSummary();
    });

    // Sync selectedItems with myConditions
    watch(myConditions, async () => {
      isUpdatingFromConditions.value = true;
      selectedItems.value = myConditions.value
        .map((c) => facetSummary.value.find((item) => item.facet.toLowerCase() === String(c.value).toLowerCase()))
        .filter((item): item is FacetSummaryResponse => item !== undefined)
        .map((item) => ({
          ...item,
          isSelectable: true,
          name: valueDisplayName(props.field, item.facet),
        }));
      // Reset flag on next tick to allow subsequent user interactions
      await nextTick();
      isUpdatingFromConditions.value = false;
    }, { deep: true });

    // Watch for changes in selectedItems and update conditions
    watch(selectedItems, (newSelected) => {
      // Don't emit if we're just syncing from external condition changes
      if (isUpdatingFromConditions.value) {
        return;
      }
      
      const newConditions = [
        ...otherConditions.value,
        ...newSelected
          .filter((item) => item.isSelectable)
          .map((item) => ({
            op: '==',
            field: props.field,
            value: item.facet,
            table: props.table,
          })),
      ];
      emit('select', { conditions: newConditions });
    }, { deep: true });

    onMounted(async () => {
      await fetchFacetSummaryUnconditional();
      /* Enable loading bar after 2 seconds of no load, to avoid overly noisy facet dialogs */
      window.setTimeout(() => { createdDelay.value = true; }, 2000);
    });

    return {
      filterText,
      createdDelay,
      selectedItems,
      tableHeaders,
      facetSummaryAggregate,
      myConditions,
      otherConditions,
      fieldDisplayName,
    };
  },
});
</script>

<template>
  <div class="match-list-table">
    <v-text-field
      v-model="filterText"
      solo
      label="search"
      clearable
      class="px-3 my-3"
      dense
      hide-details
      variant="outlined"
      flat
      append-icon="mdi-magnify"
    />
    <v-data-table
      v-model="selectedItems"
      density="compact"
      show-select
      height="355px"
      :items-per-page="10"
      :search="filterText"
      item-value="facet"
      return-object
      :items="facetSummaryAggregate"
      :headers="tableHeaders"
      :no-data-text="'Data is loading.'"
      :loading="facetSummaryAggregate.length === 0 && createdDelay"
      :loading-text="'Data is loading and could take a while.'"
    >
      <template #[`item.name`]="{ item }">
        <span :class="{ 'text-grey': !item.isSelectable }">
          {{ fieldDisplayName(item.name) }}
        </span>
      </template>
    </v-data-table>
  </div>
</template>
