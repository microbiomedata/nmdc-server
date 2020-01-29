<template>
  <GChart
    :settings="{
      packages: ['geochart'],
      mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
    }"
    type="GeoChart"
    :data="geoChartMarkerData"
    :options="geoChartMarkerOptions"
  />
</template>

<script>
import colors from 'vuetify/lib/util/colors';
import { GChart } from 'vue-google-charts';

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
