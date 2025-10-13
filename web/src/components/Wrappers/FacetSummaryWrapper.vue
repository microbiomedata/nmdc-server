<script>
import { defineComponent } from 'vue';
import FacetSummary from '@/mixins/FacetSummary';

export default defineComponent({
  mixins: [FacetSummary],
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
