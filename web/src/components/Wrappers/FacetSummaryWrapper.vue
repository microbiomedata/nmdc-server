<script setup lang="ts">
import { computed, watch, ref } from 'vue';
// @ts-ignore
import { valueDisplayName } from '@/util';
import { api, Condition, FacetSummaryResponse } from '@/data/api';

const props = defineProps<{
  field: string,
  table: string,
  useAllConditions: boolean,
  conditions: Condition[],
}>()

const facetSummary = ref<FacetSummaryResponse[] | null>(null);
const facetSummaryUnconditional = ref<FacetSummaryResponse[] | null>(null);
const errorMessage = ref<string | null>(null);

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
    errorMessage.value = 'Could not retrieve summary values with conditions';
  }
};

// Fetch unconditional facet summary
const fetchFacetSummaryUnconditional = async () => {
  try {
    facetSummaryUnconditional.value = await api.getFacetSummary(props.table, props.field, []);
    errorMessage.value = null;
  } catch (_error) {
    console.error('Error fetching facet summary unconditional:', _error);
    facetSummaryUnconditional.value = null;
    errorMessage.value = 'Could not retrieve summary values';
  }
};

// Computed property for facetSummaryAggregate
const facetSummaryAggregate = computed(() => {
  const currentFacetSummary = facetSummary.value;
  if (!currentFacetSummary) {
    return null;
  }
  const aggregate = currentFacetSummary
    .map((item) => ({
      ...item,
      isSelectable: true,
      name: valueDisplayName(props.field, item.facet),
    }));
  
  if (facetSummaryUnconditional.value) {
    aggregate.concat(facetSummaryUnconditional.value
      .filter((item1) => !currentFacetSummary.some((item2) => item1.facet === item2.facet))
      .map((item) => ({
        ...item,
        count: 0,
        isSelectable: false,
        name: valueDisplayName(props.field, item.facet),
      })));
  }
  return aggregate;
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
