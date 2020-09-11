<template>
  <GChart
    ref="chart"
    type="ColumnChart"
    :data="chartData"
    :events="chartEvents"
    :options="barChartOptions"
  />
</template>

<script>
import { GChart } from 'vue-google-charts';

export default {
  name: 'DateHistogram',
  components: {
    GChart,
  },
  props: {
    facetSummary: {
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
  computed: {
    chartEvents() {
      return {
        select: () => {
          const chart = this.$refs.chart.chartObject;
          const selection = chart.getSelection();
          if (selection.length === 1) {
            const value = this.facetSummary[selection[0].row];
            this.$emit('selected', {
              type: this.table,
              conditions: [{
                field: this.field,
                op: '==',
                value: value.facet,
                table: this.table,
              }],
            });
          }
        },
      };
    },
    chartData() {
      return [
        ['date', 'count'],
        ...this.facetSummary.map(({ count, facet }) => [new Date(facet), count]),
      ];
    },
    barChartOptions() {
      return {
        height: 160,
        chartArea: {
          left: 50,
          width: '100%',
          height: '60%',
        },
        explorer: {
          actions: ['dragToZoom', 'rightClickToReset'],
          axis: 'horizontal',
          keepInBounds: true,
        },
        colors: [this.$vuetify.theme.currentTheme.accent],
        legend: {
          position: 'none',
        },
        annotations: { alwaysOutside: true, stem: { color: 'transparent' } },
        isStacked: true,
      };
    },
  },
};
</script>
