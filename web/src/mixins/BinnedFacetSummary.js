import { computed } from 'vue';
import { computedAsync } from '@vueuse/core';
import { api } from '../data/api';

import SegmentConditions from './SegmentConditions';

export default {
  mixins: [SegmentConditions],

  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String,
      required: true,
    },
    useAllConditions: {
      type: Boolean,
      default: false,
    },
    conditions: {
      type: Array,
      default: () => [],
    },
  },

  setup(props) {
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
      { bins: [], facets: [] }
    );

    // Async computed for facetSummaryUnconditional
    const facetSummaryUnconditional = computedAsync(
      async () => api.getBinnedFacet(props.table, props.field, []),
      { bins: [], facets: [] }
    );

    return {
      facetSummary,
      facetSummaryUnconditional,
      otherConditions,
      myConditions,
    };
  },
};
