<script>
import Vue from 'vue';
import BinnedSummary from '@/mixins/BinnedFacetSummary';

export default Vue.extend({
  mixins: [BinnedSummary],
});
</script>

<template>
  <div>
    <slot
      v-bind="{
        facetSummary,
        field,
        table,
        myConditions,
        otherConditions,
      }"
    />
  </div>
</template>
