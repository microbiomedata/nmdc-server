import { mapGetters } from 'vuex';
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
  },

  data() {
    return {
      facetSummary: [],
    };
  },

  computed: mapGetters(['conditions']),

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
  },
};
