<script>
import Vue from 'vue';
import FacetSummary from '@/mixins/FacetSummary';

export default Vue.extend({
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
        myConditions,
        otherConditions,
        table,
      }"
    />
  </div>
</template>
