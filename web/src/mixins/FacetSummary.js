import { mapGetters } from 'vuex';
import { valueDisplayName } from '@/util';
import { api } from '@/data/api';

import SegmentConditions from './SegmentConditions';

export default {
  mixins: [SegmentConditions],

  data() {
    return {
      facetSummary: [],
      facetSummaryUnconditional: [],
      useAllConditions: false,
    };
  },

  computed: {
    ...mapGetters(['conditions']),
    facetSummaryAggregate() {
      return this.facetSummary
        .map((item) => ({
          ...item,
          isSelectable: true,
          name: valueDisplayName(this.field, item.facet),
        }))
        .concat(this.facetSummaryUnconditional
          .filter((item1) => !this.facetSummary.some((item2) => item1.facet === item2.facet))
          .map((item) => ({
            ...item,
            count: 0,
            isSelectable: false,
            name: valueDisplayName(this.field, item.facet),
          })));
    },
  },

  asyncComputed: {
    facetSummary: {
      get() {
        return api.getFacetSummary(
          this.table,
          this.field,
          this.otherConditions
            .concat(this.useAllConditions ? this.myConditions : []),
        );
      },
      default: [],
    },
    facetSummaryUnconditional: {
      get() {
        return api.getFacetSummary(
          this.table,
          this.field,
          [],
        );
      },
      default: [],
    },
  },
};
