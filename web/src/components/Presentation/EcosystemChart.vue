<template>
  <GChart
    ref="chart"
    type="BarChart"
    :data="barChartData"
    :options="barChartOptions"
    :events="chartEvents"
  />
</template>

<script>
import { GChart } from 'vue-google-charts';

import { ecosystems } from '@/encoding';

export default {
  name: 'EcosystemChart',
  components: {
    GChart,
  },
  props: {
    type: {
      type: String,
      default: null,
    },
    data: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      ecosystems,
      chartEvents: {
        select: () => {
          const chart = this.$refs.chart.chartObject;
          const selection = chart.getSelection();
          if (selection.length === 1) {
            const [value] = this.barChartData[selection[0].row + 1];
            let field = 'ecosystem';
            if (['Aquatic', 'Terrestrial'].includes(value)) {
              field = 'ecosystem_category';
            }
            this.$emit('selected', {
              type: this.type,
              conditions: [{
                field, op: '==', value, table: this.type,
              }],
            });
          }
        },
      },
    };
  },
  computed: {
    barChartData() {
      const hist = {};
      this.data.forEach((sample) => {
        if (sample.ecosystem === undefined) {
          return;
        }
        const colorIndex = this.ecosystems.findIndex(
          (eco) => (eco.name === sample.ecosystem) || (eco.name === sample.ecosystem_category),
        );
        if (hist[colorIndex] === undefined) {
          hist[colorIndex] = 0;
        }
        hist[colorIndex] += 1;
      });
      return [
        ['Category', 'Samples', { role: 'style' }, { role: 'annotation' }],
        ...Object.keys(hist).map(
          (bin) => [this.ecosystems[+bin].name, hist[bin], this.ecosystems[+bin].color, hist[bin]],
        ),
      ];
    },
    barChartOptions() {
      return {
        height: 400,
        bar: { groupWidth: 30 },
        chartArea: {
          left: 100, right: 50, top: 100, width: '90%', height: '50%',
        },
        hAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
          gridlines: {
            count: 0,
          },
          ticks: [],
          baseline: 0,
          baselineColor: 'transparent',
          viewWindowMode: 'maximized',
        },
        vAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
        },
        legend: { position: 'none' },
        annotations: { alwaysOutside: true, stem: { color: 'transparent' } },
      };
    },
  },
};
</script>
