<script>
import { defineComponent, computed, watch, ref } from 'vue';
import { valueDisplayName } from '@/util';
import { api, FacetSummaryResponse } from '@/data/api';

export default defineComponent({
  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String,
      required: true,
    },
    useAllConditions: {
      type: Boolean,
      default: false,
    },
    conditions: {
      type: Array,
      default: () => [],
    },
  },

  setup(props) {
    const facetSummary = ref<FacetSummaryResponse[] | null>(null);
    const facetSummaryUnconditional = ref(null);
    const errorMessage = ref(null);
    
    // Computed properties for conditions (from SegmentConditions mixin logic)
    const otherConditions = computed(() => 
      props.conditions.filter((c) => (c.field !== props.field) || (c.table !== props.table))
    );
    
    const myConditions = computed(() => 
      props.conditions.filter((c) => (c.field === props.field) && (c.table === props.table))
    );

    // Fetch facet summary based on conditions
    const fetchFacetSummary = async () => {
      const conditions = otherConditions.value.concat(
        props.useAllConditions ? myConditions.value : []
      );
      try {
        const result = await api.getFacetSummary(props.table, props.field, conditions);
        // Create a new array reference to trigger reactivity
        facetSummary.value = [...result];
        errorMessage.value = null;
      } catch (_error) {
        facetSummary.value = null;
        errorMessage.value = 'Error fetching facet summary';
      }
    };

    // Fetch unconditional facet summary
    const fetchFacetSummaryUnconditional = async () => {
      try {
        facetSummaryUnconditional.value = await api.getFacetSummary(props.table, props.field, []);
        errorMessage.value = null;
      } catch (_error) {
        facetSummaryUnconditional.value = null;
        errorMessage.value = 'Error fetching facet summary';
      }
    };

    // Computed property for facetSummaryAggregate
    const facetSummaryAggregate = computed(() => {
      return facetSummary.value
        .map((item) => ({
          ...item,
          isSelectable: true,
          name: valueDisplayName(props.field, item.facet),
        }))
        .concat(facetSummaryUnconditional.value
          .filter((item1) => !facetSummary.value.some((item2) => item1.facet === item2.facet))
          .map((item) => ({
            ...item,
            count: 0,
            isSelectable: false,
            name: valueDisplayName(props.field, item.facet),
          })));
    });

    // Watch for changes in conditions with deep: true
    watch(
      [otherConditions, myConditions, () => props.useAllConditions],
      () => {
        fetchFacetSummary();
      },
      { deep: true, immediate: true }
    );

    // Fetch unconditional data once on mount
    fetchFacetSummaryUnconditional();

    return {
      facetSummary,
      facetSummaryAggregate,
      facetSummaryUnconditional,
      field: props.field,
      conditions: props.conditions,
      myConditions,
      otherConditions,
      table: props.table,
      errorMessage,
    };
  },
});
</script>

<template>
  <div>
    <slot
      v-bind="{
        facetSummary,
        facetSummaryAggregate,
        facetSummaryUnconditional,
        field,
        conditions,
        myConditions,
        otherConditions,
        table,
        errorMessage,
      }"
    />
  </div>
</template>
