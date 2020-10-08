<script>
import { flatten } from 'lodash';
import moment from 'moment';

import ChartContainer from '@/components/charts/ChartContainer.vue';
import Histogram from '@/components/charts/Histogram/Histogram.vue';
import RangeSlider from '@/components/charts/RangeSlider.vue';

export default {
  name: 'DateHistogram',
  components: {
    ChartContainer,
    Histogram,
    RangeSlider,
  },
  props: {
    facetSummary: {
      type: Array,
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
      range: [0, new Date().valueOf()],
      min: 0,
      max: (new Date()).valueOf(),
      /* Whether to reset the range based on an external update */
      loadOnNextUpdate: true,
    };
  },

  computed: {
    data() {
      return flatten(this.facetSummary.map(
        ({ facet, count }) => Array(count).fill(new Date(facet)),
      ));
    },
    tickfmt() {
      return (d) => moment(d).format('l');
    },
    round() {
      return (d) => (new Date(moment(d).format('YYYY-MM-DDT00:00:00.000'))).valueOf();
    },
  },

  watch: {
    facetSummary() {
      let nextTick = () => {
        [this.min, this.max] = this.$refs.histogram.rangeScale.range();
        this.range = [this.min, this.max];
        this.extent = this.range;
      };
      if (this.loadOnNextUpdate) {
        if (this.myConditions.length === 1) {
          const [condition] = this.myConditions;
          this.selectedOption = condition.op;
          if (condition.op === 'between' && typeof condition.value === 'object') {
            nextTick = () => {
              [this.min, this.max] = this.$refs.histogram.rangeScale.range();
              this.range = condition.value.map((c) => (new Date(c)).valueOf());
            };
          }
        }
        this.$nextTick(nextTick);
        this.loadOnNextUpdate = false;
      }
    },
    myConditions() {
      if (this.myConditions.length !== 0) {
        this.loadOnNextUpdate = true;
      } else {
        this.range = [this.min, this.max];
      }
    },
  },

  methods: {
    afterDrag() {
      this.loadOnNextUpdate = false;
      if (this.range[0] !== this.min || this.range[1] !== this.max) {
        const values = this.$refs.histogram.scaledRange;
        this.$emit('select', {
          type: this.table,
          conditions: [
            ...this.otherConditions,
            {
              field: this.field,
              op: 'between',
              value: values.map((d) => moment(d).format('YYYY-MM-DDT00:00:00.000')),
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
};
</script>

<template>
  <div class="histogram mb-6">
    <ChartContainer v-if="data.length > 0">
      <template #default="{ width, height }">
        <Histogram
          ref="histogram"
          v-bind="{ width, height, data, range }"
        />
      </template>
      <template #below="{ width }">
        <range-slider
          v-model="range"
          :max="max"
          :min="min"
          :width="width"
          :height="40"
          :fmt="tickfmt"
          :round="round"
          @end="afterDrag"
        />
      </template>
    </ChartContainer>
  </div>
</template>

<style scoped>
.histogram {
  width: 100%;
}
</style>
