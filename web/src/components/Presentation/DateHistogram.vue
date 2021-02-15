<script>
import Vue from 'vue';
import moment from 'moment';

import ChartContainer from '@/components/Presentation/ChartContainer.vue';
import Histogram2 from '@/components/Presentation/Histogram2.vue';

export default Vue.extend({
  name: 'DateHistogram',
  components: {
    ChartContainer,
    Histogram2,
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
    facetSummaryUnconditional() {
      // Derive min/max from full range
      const setMinMax = () => {
        this.min = Date.parse(this.facetSummaryUnconditional.bins[0]);
        this.max = Date.parse(
          this.facetSummaryUnconditional.bins[this.facetSummaryUnconditional.bins.length - 1],
        );
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
  },
});
</script>

<template>
  <div class="histogram">
    <ChartContainer v-if="facetSummary && range !== null">
      <template #default="{ width, height }">
        <Histogram2
          ref="histogram"
          v-bind="{ width, height, data: facetSummary, range }"
        />
      </template>
      <template #below>
        <div class="mx-4">
          <v-range-slider
            v-model="range"
            :min="min"
            :max="max"
            hide-details
            color="primary"
            thumb-color="accent"
            @change="afterDrag"
          />
          <div class="d-flex">
            <span>{{ moment(range[0]).format('MM/DD/YYYY') }}</span>
            <v-spacer />
            <span>{{ moment(range[1]).format('MM/DD/YYYY') }}</span>
          </div>
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
