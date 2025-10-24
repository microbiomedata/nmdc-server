import { valueDisplayName } from '@/util';
import { api } from '@/data/api';

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
      facetSummaryUnconditional: [],
    };
  },

  watch: {
    // Watch for changes in conditions and refetch data
    otherConditions: {
      handler() {
        console.log('Conditions changed, refetching facet summary');
        this.fetchFacetSummary();
      },
      deep: true,
      immediate: true,
    },
    myConditions: {
      handler() {
        console.log('My conditions changed, refetching facet summary');
        this.fetchFacetSummary();
      },
      deep: true,
    },
    useAllConditions() {
      this.fetchFacetSummary();
    },
  },

  async created() {
    await this.fetchFacetSummaryUnconditional();
  },

  methods: {
    async fetchFacetSummary() {
      try {
        const conditions = this.otherConditions.concat(this.useAllConditions ? this.myConditions : []);
        console.log('FETCHING CONDITIONAL FACET SUMMARY with conditions:', conditions);
        this.facetSummary = await api.getFacetSummary(
          this.table,
          this.field,
          conditions,
        );
      } catch (error) {
        console.error('Error fetching facet summary:', error);
        this.facetSummary = [];
      }
    },

    async fetchFacetSummaryUnconditional() {
      try {
        console.log('FETCHING UNCONDITIONAL FACET SUMMARY');
        this.facetSummaryUnconditional = await api.getFacetSummary(
          this.table,
          this.field,
          [],
        );
      } catch (error) {
        console.error('Error fetching unconditional facet summary:', error);
        this.facetSummaryUnconditional = [];
      }
    },
  },

  computed: {
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
};
