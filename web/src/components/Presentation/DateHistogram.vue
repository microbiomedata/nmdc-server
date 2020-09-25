<script>
import { flatten } from 'lodash';
import moment from 'moment';

import ChartContainer from '@/components/charts/ChartContainer.vue';
import Histogram from '@/components/charts/Histogram/Histogram.vue';

export default {
  name: 'DateHistogram',
  components: {
    ChartContainer,
    Histogram,
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
      range: [0, 100],
      min: 0,
      max: 100,
      loaded: false,
    };
  },

  computed: {
    data() {
      return flatten(this.facetSummary.map(
        ({ facet, count }) => Array(count).fill(new Date(facet)),
      ));
    },
  },

  watch: {
    facetSummary() {
      if (!this.loaded) {
        if (this.myConditions.length === 1) {
          const [condition] = this.myConditions;
          this.selectedOption = condition.op;
          if (condition.op === 'between' && typeof condition.value === 'object') {
            this.$nextTick(() => {
              /* wait for the data change to propogate into the child */
              const inverter = this.$refs.histogram.rangeScale.invert;
              this.range = condition.value.map((c) => Math.round(inverter(new Date(c)).valueOf()));
            });
          }
        }
        this.loaded = true;
      }
    },
    myConditions() {
      if (this.myConditions.length === 0) {
        this.range = [0, 100];
      }
    },
  },

  methods: {
    afterDrag() {
      if (this.range[0] !== 0 || this.range[1] !== 100) {
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
    <ChartContainer
      style="margin: 0 auto;"
    >
      <template #default="{ width, height }">
        <Histogram
          ref="histogram"
          v-bind="{ width, height, data, range }"
        />
      </template>
      <template #below>
        <v-range-slider
          v-model="range"
          :max="max"
          :min="min"
          hide-details
          class="align-center"
          color="accent"
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
