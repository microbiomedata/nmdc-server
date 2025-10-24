<script>
import { defineComponent, computed, watch, ref } from 'vue';
import { valueDisplayName } from '@/util';
import { api } from '@/data/api';

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
    const facetSummary = ref([]);
    const facetSummaryUnconditional = ref([]);
    
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
      console.log('FETCHING CONDITIONAL FACET SUMMARY with conditions:', conditions);
      try {
        const result = await api.getFacetSummary(props.table, props.field, conditions);
        // Create a new array reference to trigger reactivity
        facetSummary.value = [...result];
        console.log('Updated facetSummary:', facetSummary.value);
      } catch (error) {
        console.error('Error fetching facet summary:', error);
        facetSummary.value = [];
      }
    };

    // Fetch unconditional facet summary
    const fetchFacetSummaryUnconditional = async () => {
      console.log('FETCHING UNCONDITIONAL FACET SUMMARY');
      try {
        facetSummaryUnconditional.value = await api.getFacetSummary(props.table, props.field, []);
      } catch (error) {
        console.error('Error fetching unconditional facet summary:', error);
        facetSummaryUnconditional.value = [];
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
        console.log('Conditions changed, refetching facet summary');
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
      }"
    />
  </div>
</template>
