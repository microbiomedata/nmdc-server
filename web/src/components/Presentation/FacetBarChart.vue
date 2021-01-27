<template>
  <GChart
    ref="chart"
    type="BarChart"
    :data="chartData"
    :options="barChartOptions"
    :events="chartEvents"
  />
</template>

<script>
import Vue from 'vue';
import { GChart } from 'vue-google-charts';
import { fieldDisplayName } from '@/util';
import { ecosystems } from '@/encoding';

export default Vue.extend({
  name: 'FacetBarChart',
  components: {
    GChart,
  },
  props: {
    showTitle: {
      type: Boolean,
      default: true,
    },
    showBaseline: {
      type: Boolean,
      default: true,
    },
    leftMargin: {
      type: Number,
      default: 80,
    },
    rightMargin: {
      type: Number,
      default: 40,
    },
    chart: {
      type: String,
      default: null,
    },
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
    stacked: {
      type: [Boolean, String],
      default: true,
    },
    facetSummary: {
      type: Array,
      required: true,
    },
    facetSummaryUnconditional: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      chartEvents: {
        select: () => {
          const chart = this.$refs.chart.chartObject;
          const selection = chart.getSelection();
          if (selection.length === 1) {
            const [value] = this.chartData[selection[0].row + 1];
            this.$emit('selected', {
              conditions: [{
                field: this.field,
                op: '==',
                value,
                table: this.table,
              }],
            });
          }
        },
      },
    };
  },
  computed: {
    chartData() {
      return [
        [
          { label: fieldDisplayName(this.field) },
          { label: 'Match', role: 'data' },
          { role: 'scope' },
          { role: 'style' },
          { label: 'No Match', role: 'data' },
          { role: 'scope' },
          { role: 'style' },
          { role: 'annotation' },
        ],
        ...this.facetSummaryUnconditional.map(
          (facet) => [
            facet.facet,
            (this.facetSummary.find((e) => e.facet === facet.facet) || {}).count || 0,
            true,
            (
              ecosystems.find((e) => e.name === facet.facet)
              || { color: this.$vuetify.theme.currentTheme.primary }
            ).color,
            facet.count - ((this.facetSummary.find(
              (e) => e.facet === facet.facet,
            ) || {}).count || 0),
            false,
            'lightgrey',
            (this.facetSummary.find((e) => e.facet === facet.facet) || {}).count || 0,
          ],
        ),
      ];
    },
    barChartOptions() {
      return {
        height: this.height,
        chartArea: {
          left: this.leftMargin,
          right: this.rightMargin,
          top: 15,
          width: '90%',
          height: '80%',
        },
        hAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
          gridlines: {
            count: 0,
          },
          ticks: [],
          baselineColor: this.showBaseline ? 'black' : 'transparent',
          baseline: 0,
          viewWindowMode: 'maximized',
        },
        vAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
        },
        legend: { position: 'none' },
        annotations: { alwaysOutside: true, stem: { color: 'transparent' } },
        title: this.showTitle ? fieldDisplayName(this.field) : null,
        isStacked: true,
      };
    },
  },
});
</script>
