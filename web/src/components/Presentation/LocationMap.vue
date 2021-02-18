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
import Vue from 'vue';
import { GChart } from 'vue-google-charts';

import { api } from '@/data/api';
import { ecosystems } from '@/encoding';

// This vis only works for biosample;
const table = 'biosample';

export default Vue.extend({
  name: 'LocationMap',
  components: {
    GChart,
  },
  props: {
    conditions: {
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
            this.$emit('selected', {
              conditions: [
                {
                  field: 'latitude', op: '==', value: lat, table,
                },
                {
                  field: 'longitude', op: '==', value: lon, table,
                },
              ],
            });
          }
        },
      },
    };
  },
  asyncComputed: {
    async geoChartMarkerData() {
      const hist = {};
      const data = await api.getEnvironmentGeospatialAggregation(this.conditions);
      data.forEach((sample) => {
        const latLon = `${sample.latitude}:${sample.longitude}:${this.ecosystems.findIndex(
          (eco) => (eco.name === sample.ecosystem) || (eco.name === sample.ecosystem_category),
        )}`;
        if (hist[latLon] === undefined) {
          hist[latLon] = 0;
        }
        hist[latLon] += sample.count;
      });
      return [
        ['Latitude', 'Longitude', 'Color', 'Size'],
        ...Object.keys(hist).map((latLon) => [...latLon.split(':').map((d) => +d), hist[latLon]]),
      ];
    },
  },
  computed: {
    geoChartMarkerOptions() {
      return {
        displayMode: 'markers',
        height: 360,
        colorAxis: {
          minValue: 0,
          maxValue: 3,
          colors: this.ecosystems.map((eco) => eco.color),
        },
        backgroundColor: '#ffffff',
        datalessRegionColor: '#efefef',
        defaultColor: '#f5f5f5',
        legend: 'none',
      };
    },
  },
});
</script>
