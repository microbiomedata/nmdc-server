<script>
import { defineComponent } from 'vue';
import BinnedSummary from '@/mixins/BinnedFacetSummary';

export default defineComponent({
  mixins: [BinnedSummary],
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
      }"
    />
  </div>
</template>
