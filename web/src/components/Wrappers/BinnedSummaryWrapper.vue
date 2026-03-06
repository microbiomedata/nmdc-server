<script setup lang="ts">
import { computed } from 'vue';
import { computedAsync } from '@vueuse/core';
import { api, Condition, EntityType } from '@/data/api';

const props = withDefaults(defineProps<{
  field: string;
  table: EntityType;
  useAllConditions?: boolean;
  conditions?: Condition[];
}>(), {
  useAllConditions: false,
  conditions: () => [],
});

// Computed properties for conditions (from SegmentConditions mixin logic)
const otherConditions = computed(() =>
  props.conditions.filter((c) => (c.field !== props.field) || (c.table !== props.table))
);

const myConditions = computed(() =>
  props.conditions.filter((c) => (c.field === props.field) && (c.table === props.table))
);

// Async computed for facetSummary
const facetSummary = computedAsync(
  async () => {
    const conditions = otherConditions.value.concat(
      props.useAllConditions ? myConditions.value : []
    );
    return api.getBinnedFacet(props.table, props.field, conditions);
  },
  null
);

// Async computed for facetSummaryUnconditional
const facetSummaryUnconditional = computedAsync(
  async () => api.getBinnedFacet(props.table, props.field, []),
  null
);

const errorMessage = computed(() => {
  if (facetSummaryUnconditional.value === null) {
    return 'Could not retrieve summary values';
  }
  if (facetSummary.value === null) {
    return 'Could not retrieve summary values with conditions';
  }
  return null;
});

</script>

<template>
  <div>
    <slot
      v-bind="{
        facetSummary,
        facetSummaryUnconditional,
        field,
        table,
        myConditions,
        otherConditions,
        errorMessage,
      }"
    />
  </div>
</template>
