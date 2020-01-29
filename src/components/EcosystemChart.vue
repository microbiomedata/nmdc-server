<template>
  <GChart
    type="BarChart"
    :data="barChartData"
    :options="barChartOptions"
  />
</template>

<script>
import colors from 'vuetify/lib/util/colors';
import { GChart } from 'vue-google-charts';

// import encoding from './encoding';

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
  data: () => ({
    ecosystems: [
      {
        name: 'Host-associated',
        color: colors.red.base,
      },
      {
        name: 'Aquatic',
        color: colors.lightBlue.base,
      },
      {
        name: 'Terrestrial',
        color: colors.lightGreen.darken2,
      },
      {
        name: 'Engineered',
        color: colors.orange.base,
      },
    ],
  }),
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
