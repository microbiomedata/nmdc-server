<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue';
import { api, BinResponse, Condition, EntityType } from '@/data/api';
import useRequest from '@/use/useRequest';

const props = withDefaults(defineProps<{
  field: string;
  table: EntityType;
  useAllConditions?: boolean;
  conditions?: Condition[];
}>(), {
  useAllConditions: false,
  conditions: () => [],
});
const facetSummary = ref<BinResponse<string | number> | null>(null);
const facetSummaryUnconditional = ref<BinResponse<string | number> | null>(null);
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

const otherConditions = computed(() =>
  props.conditions.filter((c) => (c.field !== props.field) || (c.table !== props.table))
);

const myConditions = computed(() =>
  props.conditions.filter((c) => (c.field === props.field) && (c.table === props.table))
);

watchEffect(async () => {
  const { table, field, useAllConditions } = props;
  const conditions = otherConditions.value.concat(useAllConditions ? myConditions.value : []);
  facetSummary.value = await conditionalRequest.request(
    () => api.getBinnedFacet(table, field, conditions),
  );
});

watchEffect(async () => {
  const { table, field } = props;
  facetSummaryUnconditional.value = await unconditionalRequest.request(
    () => api.getBinnedFacet(table, field, []),
  );
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
        error,
        loading,
      }"
    />
  </div>
</template>
