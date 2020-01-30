<template>
  <GChart
    ref="chart"
    :settings="{
      packages: ['geochart'],
    }"
    type="GeoChart"
    :data="geoChartMarkerData"
    :options="geoChartMarkerOptions"
    :events="chartEvents"
  />
</template>

<script>
import colors from 'vuetify/lib/util/colors';
import { GChart } from 'vue-google-charts';

import { ecosystems } from './encoding';

export default {
  name: 'LocationMap',
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
      ecosystems,
      chartEvents: {
        select: () => {
          const chart = this.$refs.chart.chartObject;
          const selection = chart.getSelection();
          if (selection.length === 1) {
            const [lat, lon] = this.geoChartMarkerData[selection[0].row + 1];
            this.$emit('selected', { field: 'latitude', value: lat });
            this.$emit('selected', { field: 'longitude', value: lon });
          }
        },
      },
    };
  },
  computed: {
    geoChartMarkerData() {
      const hist = {};
      this.data.forEach((sample) => {
        if (sample.latitude === undefined || sample.longitude === undefined) {
          return;
        }
        const latLon = `${sample.latitude}:${sample.longitude}:${this.ecosystems.findIndex(
          (eco) => (eco.name === sample.ecosystem) || (eco.name === sample.ecosystem_category),
        )}`;
        if (hist[latLon] === undefined) {
          hist[latLon] = 0;
        }
        hist[latLon] += 1;
      });
      return [
        ['Latitude', 'Longitude', 'Color', 'Size'],
        ...Object.keys(hist).map((latLon) => [...latLon.split(':').map((d) => +d), hist[latLon]]),
      ];
    },
    geoChartMarkerOptions() {
      return {
        displayMode: 'markers',
        height: 400,
        colorAxis: {
          minValue: 0,
          maxValue: 3,
          colors: this.ecosystems.map((eco) => eco.color),
        },
        backgroundColor: colors.lightBlue.lighten3,
        datalessRegionColor: '#eeeeee',
        defaultColor: '#f5f5f5',
        legend: 'none',
      };
    },
  },
};
</script>
