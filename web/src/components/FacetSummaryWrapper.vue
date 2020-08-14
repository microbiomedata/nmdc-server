<script>
import { mapState, mapGetters } from 'vuex';

export default {
  props: {
    table: {
      type: String,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
  },

  data() {
    return {
      facetSummary: [],
      facetSummaryUnconditional: [],
    };
  },

  computed: {
    ...mapState(['facetSummaries', 'facetSummariesUnconditional']),
    ...mapGetters(['conditions']),
  },

  watch: {
    // Vuex will invalidate this cache when necessary,
    // so we can listen to the object to know when to reload.
    facetSummaries: {
      handler: 'updateFacetCharts',
      deep: true,
    },
  },

  methods: {
    async updateFacetCharts() {
      this.$store.dispatch('fetchFacetSummary', {
        field: this.field,
        type: this.table,
        conditions: this.conditions,
      });
      const newFacetSummary = this.facetSummaries[this.table][this.field];
      if (newFacetSummary) {
        this.facetSummary = newFacetSummary;
        this.facetSummaryUnconditional = this.facetSummariesUnconditional[this.table][this.field];
      }
    },
  },
};
</script>

<template>
  <div>
    <slot v-bind="{ facetSummary, facetSummaryUnconditional, table, field }" />
  </div>
</template>
