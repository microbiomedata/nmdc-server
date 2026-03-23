import { computed, Ref } from 'vue';
import { Condition, EntityType } from '@/data/api';

export default function useFacetSummaryData({
  field,
  table,
  conditions,
}: {
  field: Ref<string>,
  table: Ref<EntityType>,
  conditions: Ref<Condition[]>,
}) {
  const otherConditions = computed(() => (
    // conditions from OTHER fields
    conditions.value.filter((c) => (c.field !== field.value) || (c.table !== table.value))
  ));

  const myConditions = computed(() => (
    // conditions that match our field.
    conditions.value.filter((c) => (c.field === field.value) && (c.table === table.value))
  ));

  return {
    otherConditions,
    myConditions,
  };
}
