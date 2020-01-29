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

import encoding from './encoding';

export default {
  name: 'EcosystemChart',
  components: {
    GChart,
  },
  props: {
    data: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      ecosystems: encoding.ecosystems,
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
            this.$emit('selected', { field, value });
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
        ['Category', 'Samples', { role: 'style' }],
        ...Object.keys(hist).map(
          (bin) => [this.ecosystems[+bin].name, hist[bin], this.ecosystems[+bin].color],
        ),
      ];
    },
    barChartOptions() {
      return {
        chartArea: {
          left: 200, top: 10, width: '90%', height: '90%',
        },
        hAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
        },
        vAxis: {
          textStyle: {
            fontName: 'Roboto',
          },
        },
        legend: { position: 'none' },
      };
    },
  },
};
</script>
