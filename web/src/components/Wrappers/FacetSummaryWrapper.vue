<script setup lang="ts">
import { computed, watch, ref } from 'vue';
// @ts-ignore
import { valueDisplayName } from '@/util';
import { api, Condition, EntityType, FacetSummaryResponse } from '@/data/api';
import useRequest from '@/use/useRequest';

const props = defineProps<{
  field: string,
  table: EntityType,
  useAllConditions?: boolean,
  conditions: Condition[],
}>()

const facetSummary = ref<FacetSummaryResponse[] | null>(null);
const facetSummaryUnconditional = ref<FacetSummaryResponse[] | null>(null);
const conditionalRequest = useRequest();
const unconditionalRequest = useRequest();
const error = computed(() => {
  if (unconditionalRequest.error.value) {
    return 'Could not retrieve summary values';
  } else if (conditionalRequest.error.value) {
    return 'Could not retrieve summary values with conditions';
  } 
  return null;
});
const loading = computed(() => conditionalRequest.loading.value || unconditionalRequest.loading.value);

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
  facetSummary.value = await conditionalRequest.request(() => api.getFacetSummary(props.table, props.field, conditions));
};

// Fetch unconditional facet summary
const fetchFacetSummaryUnconditional = async () => {
  facetSummaryUnconditional.value = await unconditionalRequest.request(() => api.getFacetSummary(props.table, props.field, []));
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
    aggregate.push(
      ...facetSummaryUnconditional.value
        .filter((item1) => !currentFacetSummary.some((item2) => item1.facet === item2.facet))
        .map((item) => ({
          ...item,
          count: 0,
          isSelectable: false,
          name: valueDisplayName(props.field, item.facet),
        }))
    );
  }
  return aggregate;
});

// Watch for changes in conditions with deep: true
watch(
  [otherConditions, myConditions, () => props.useAllConditions],
  () => {
    fetchFacetSummary();
  },
  { immediate: true }
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
        error,
        loading,
      }"
    />
  </div>
</template>
