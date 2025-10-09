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

  data() {
    return {
      facetSummary: [],
    };
  },

  asyncComputed: {
    facetSummary: {
      get() {
        return api.getBinnedFacet(
          this.table,
          this.field,
          this.otherConditions
            .concat(this.useAllConditions ? this.myConditions : []),
        );
      },
      default: {},
    },
    facetSummaryUnconditional: {
      get() {
        return api.getBinnedFacet(
          this.table,
          this.field,
          [],
        );
      },
      default: {},
    },
  },
};
