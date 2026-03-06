<script setup lang="ts">
import { computed, ref } from 'vue';
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
const errorMessage = ref<string | null>(null);

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
    errorMessage.value = null;
    const conditions = otherConditions.value.concat(
      props.useAllConditions ? myConditions.value : []
    );
    return api.getBinnedFacet(props.table, props.field, conditions);
  },
  null,
  { onError: (_e) => { errorMessage.value = 'Could not retrieve summary values with conditions'; } },
);

// Async computed for facetSummaryUnconditional
const facetSummaryUnconditional = computedAsync(
  async () => api.getBinnedFacet(props.table, props.field, []),
  null,
  { onError: (_e) => { errorMessage.value = 'Could not retrieve summary values'; } },
);

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
