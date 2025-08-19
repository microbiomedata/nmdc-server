<script>
import Vue from 'vue';
import moment from 'moment';

import ChartContainer from '@/components/Presentation/ChartContainer.vue';
import TimeHistogram from '@/components/Presentation/TimeHistogram.vue';

export default Vue.extend({
  name: 'DateHistogram',
  components: {
    ChartContainer,
    TimeHistogram,
  },
  props: {
    facetSummary: {
      type: Object,
      required: true,
    },
    facetSummaryUnconditional: {
      type: Object,
      required: true,
    },
    otherConditions: {
      type: Array,
      required: true,
    },
    myConditions: {
      type: Array,
      required: true,
    },
    table: {
      type: String,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    height: {
      type: Number,
      default: 160,
    },
  },

  data() {
    return {
      range: null,
      min: 0,
      max: 100,
      moment,
    };
  },

  watch: {
    facetSummary() {
      // Derive min/max from full range
      const setMinMax = () => {
        const min = Date.parse(this.facetSummaryUnconditional.bins[0]);
        const max = Date.parse(
          this.facetSummaryUnconditional.bins[this.facetSummaryUnconditional.bins.length - 1],
        );
        if (Number.isNaN(min) || Number.isNaN(max)) {
          return;
        }
        this.min = min;
        this.max = max;
        this.range = [this.min, this.max];
      };
      let nextTick = setMinMax;
      if (this.myConditions.length === 1) {
        const [condition] = this.myConditions;
        if (condition.op === 'between' && typeof condition.value === 'object') {
          // If range is already set, figure it out from the condition.
          nextTick = () => {
            // but get min/max from full range anyway.
            setMinMax();
            this.range = condition.value.map((c) => (new Date(c)).valueOf());
          };
        }
      }
      this.$nextTick(() => nextTick());
    },
    myConditions() {
      if (this.myConditions.length === 0) {
        // Otherwise, reset to min/max
        this.range = [this.min, this.max];
      }
    },
  },

  methods: {
    afterDrag() {
      if (this.range[0] !== this.min || this.range[1] !== this.max) {
        this.$emit('select', {
          type: this.table,
          conditions: [
            ...this.otherConditions,
            {
              field: this.field,
              op: 'between',
              value: this.range.map((d) => moment(d).format('YYYY-MM-DDT00:00:00.000')),
              table: this.table,
            },
          ],
        });
      } else if (this.myConditions.length) {
        this.$emit('select', {
          type: this.table,
          conditions: this.otherConditions,
        });
      }
    },
    onBrushEnd(brushRange) {
      if (brushRange && (brushRange[0] !== this.min || brushRange[1] !== this.max)) {
        this.$emit('select', {
          type: this.table,
          conditions: [
            ...this.otherConditions,
            {
              field: this.field,
              op: 'between',
              value: brushRange.map((d) => moment(d).format('YYYY-MM-DDT00:00:00.000')),
              table: this.table,
            },
          ],
        });
      } else if (this.myConditions.length) {
        this.$emit('select', {
          type: this.table,
          conditions: this.otherConditions,
        });
      }
    },
  },
});
</script>

<template>
  <div class="histogram">
    <ChartContainer :height="height">
      <template #default="{ width }">
        <TimeHistogram
          ref="histogram"
          v-bind="{ width, height, selectedData: facetSummary, totalData: facetSummaryUnconditional, range: range || [] }"
          @onBrushEnd="onBrushEnd"
        />
      </template>
      <template #below>
        <div class="mx-4 d-flex">
          <v-spacer />
          <h4>Collection Date</h4>
          <v-spacer />
        </div>
      </template>
    </ChartContainer>
  </div>
</template>

<style scoped>
.histogram {
  width: 100%;
}
</style>
