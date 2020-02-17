<template>
  <GChart
    ref="chart"
    :type="chart === 'bar' ? 'BarChart' : 'PieChart'"
    :data="chartData"
    :options="chart === 'bar' ? barChartOptions : pieChartOptions"
    :events="chartEvents"
  />
</template>

<script>
import { GChart } from 'vue-google-charts';

import api from '../data/api';
import * as encoding from '../encoding';
import { fieldDisplayName } from '../util';

export default {
  name: 'FacetChart',
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
      default: 50,
    },
    chart: {
      type: String,
      default: null,
    },
    type: {
      type: String,
      default: null,
    },
    field: {
      type: String,
      default: null,
    },
    conditions: {
      type: Array,
      default: () => [],
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
              type: this.type,
              conditions: [{ field: this.field, op: '==', value }],
            });
          }
        },
      },
    };
  },
  computed: {
    facets() {
      return api.facetSummary({
        type: this.type,
        field: this.field,
        conditions: this.conditions,
        useMatchingConditions: true,
      }).filter((d) => d.count > 0);
    },
    chartData() {
      return [
        [fieldDisplayName(this.field), 'Count', { role: 'style' }, { role: 'annotation' }],
        ...this.facets.map(
          (facet) => [
            facet.value,
            facet.count,
            encoding.values[facet.value] ? encoding.values[facet.value].color : 'grey',
            facet.count,
          ],
        ),
      ];
    },
    barChartOptions() {
      return {
        height: 300,
        chartArea: {
          left: this.leftMargin, right: 40, top: 15, width: '90%', height: '90%',
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
      };
    },
    pieChartOptions() {
      return {
        height: 300,
        chartArea: {
          width: '55%',
          height: '55%',
        },
        legend: 'none',
        pieSliceText: 'label',
        slices: this.facets.map((facet) => ({ color: encoding.values[facet.value] ? encoding.values[facet.value].color : 'grey' })),
        title: this.showTitle ? fieldDisplayName(this.field) : null,
      };
    },
  },
};
</script>
