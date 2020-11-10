<template>
  <GChart
    ref="chart"
    type="Histogram"
    :data="chartData"
    :options="chartOptions"
  />
</template>

<script>
import Vue from 'vue';
import { GChart } from 'vue-google-charts';
// import { fieldDisplayName } from '@/util';
// import { ecosystems } from '@/encoding';

export default Vue.extend({
  name: 'FacetHistogramChart',
  components: {
    GChart,
  },
  props: {
    table: {
      type: String,
      default: null,
    },
    field: {
      type: String,
      default: null,
    },
    height: {
      type: Number,
      default: 200,
    },
    facetSummary: {
      type: Array,
      required: true,
    },
  },
  computed: {
    chartData() {
      return [
        ['Field', 'Value'],
        ...this.facetSummary.map(
          (facet) => [
            this.field,
            window.parseInt(facet.facet, 10),
          ],
        ),
      ];
    },
    chartOptions() {
      return {
        height: this.height,
        chartArea: {
          left: 80,
          right: 40,
          top: 40,
          bottom: 40,
          width: '100%',
          height: '80%',
        },
        hAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
          slantedText: true,
          format: 'short',
          baseline: 0,
          maxAlternation: 3,
        },
        vAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
        },
        colors: [this.$vuetify.theme.currentTheme.primary],
        legend: { position: 'none' },
        title: this.field,
        histogram: {
          maxNumBuckets: 30,
          bucketSize: 200000,
        },
      };
    },
  },
});
</script>
