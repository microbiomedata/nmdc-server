<script>
import Vue from 'vue';
import FacetSummary from '@/mixins/FacetSummary';

export default Vue.extend({
  mixins: [FacetSummary],
  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String,
      required: true,
    },
  },
});
</script>

<template>
  <div>
    <slot
      v-bind="{
        facetSummaryAggregate, facetSummary, facetSummaryUnconditional, field, table,
      }"
    />
  </div>
</template>
