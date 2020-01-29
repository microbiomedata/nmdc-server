<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartMarkerData.all"
            :options="geoChartMarkerOptions.all"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartMarkerData.host"
            :options="geoChartMarkerOptions.host"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartMarkerData.terrestrial"
            :options="geoChartMarkerOptions.terrestrial"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartMarkerData.aquatic"
            :options="geoChartMarkerOptions.aquatic"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartMarkerData.engineered"
            :options="geoChartMarkerOptions.engineered"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartData.all"
            :options="geoChartOptions.all"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartData.terrestrial"
            :options="geoChartOptions.terrestrial"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartData.aquatic"
            :options="geoChartOptions.aquatic"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartData.host"
            :options="geoChartOptions.host"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['geochart'],
              mapsApiKey: 'AIzaSyB6gTlWesrHls1rSUMQnTIOcwkspDi-wo8'
            }"
            type="GeoChart"
            :data="geoChartData.engineered"
            :options="geoChartOptions.engineered"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            type="BarChart"
            :data="barChartData"
            :options="barChartOptions"
            :events="chartEvents"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <GChart
            :settings="{
              packages: ['sankey'],
            }"
            type="Sankey"
            :data="sankeyData"
            :options="sankeyOptions"
          />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { GChart } from 'vue-google-charts';

// import biosamples from './Biosample_1000.json';
import biosamples from './schema-test-full-compact.json';
import encoding from './encoding';

const vuetifyColor = {
  red: '#f44336',
  pink: '#e91e63',
  purple: '#9c27b0',
  'deep-purple': '#673ab7',
  indigo: '#3f51b5',
  blue: '#2196f3',
  'light-blue': '#03a9f4',
  cyan: '#00bcd4',
  teal: '#009688',
  green: '#4caf50',
  'light-green': '#8bc34a',
  lime: '#cddc39',
  yellow: '#ffeb3b',
  amber: '#ffc107',
  orange: '#ff9800',
  'deep-orange': '#ff5722',
  brown: '#795548',
  'blue-grey': '#607d8b',
  grey: '#9e9e9e',
};

export default {
  name: 'HelloWorld',
  components: {
    GChart,
  },
  data: () => ({
    biosamples,
    chartEvents: {
      select: () => {
        console.log('hi');
      },
    },
  }),
  computed: {
    barChartData() {
      const hist = {};
      this.biosamples.forEach((sample) => {
        if (sample.ecosystem === undefined) {
          return;
        }
        if (hist[sample.ecosystem] === undefined) {
          hist[sample.ecosystem] = 0;
        }
        hist[sample.ecosystem] += 1;
      });
      return [
        ['Category', 'Samples', { role: 'style' }],
        ...Object.keys(hist).map(
          (bin) => [bin, hist[bin], vuetifyColor[encoding.ecosystem[bin].color]],
        ),
      ];
    },
    barChartOptions() {
      return {
        height: 400,
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
    geoChartData() {
      const hist = {
        all: {},
        terrestrial: {},
        aquatic: {},
        host: {},
        engineered: {},
      };
      this.biosamples.forEach((sample) => {
        if (sample.geographic_location === undefined) {
          return;
        }
        let country = sample.geographic_location.split(':')[0];
        if (country === 'USA') {
          country = 'United States';
        }
        if (hist.all[country] === undefined) {
          hist.all[country] = 0;
        }
        hist.all[country] += 1;
        if (sample.ecosystem === 'Engineered') {
          if (hist.engineered[country] === undefined) {
            hist.engineered[country] = 0;
          }
          hist.engineered[country] += 1;
        }
        if (sample.ecosystem === 'Host-associated') {
          if (hist.host[country] === undefined) {
            hist.host[country] = 0;
          }
          hist.host[country] += 1;
        }
        if (sample.ecosystem_category === 'Terrestrial') {
          if (hist.terrestrial[country] === undefined) {
            hist.terrestrial[country] = 0;
          }
          hist.terrestrial[country] += 1;
        }
        if (sample.ecosystem_category === 'Aquatic') {
          if (hist.aquatic[country] === undefined) {
            hist.aquatic[country] = 0;
          }
          hist.aquatic[country] += 1;
        }
      });
      return {
        all: [
          ['Country', 'Samples'],
          ...Object.keys(hist.all).map((country) => [country, hist.all[country]]),
        ],
        host: [
          ['Country', 'Samples'],
          ...Object.keys(hist.host).map((country) => [country, hist.host[country]]),
        ],
        engineered: [
          ['Country', 'Samples'],
          ...Object.keys(hist.engineered).map((country) => [country, hist.engineered[country]]),
        ],
        terrestrial: [
          ['Country', 'Samples'],
          ...Object.keys(hist.terrestrial).map((country) => [country, hist.terrestrial[country]]),
        ],
        aquatic: [
          ['Country', 'Samples'],
          ...Object.keys(hist.aquatic).map((country) => [country, hist.aquatic[country]]),
        ],
      };
    },
    geoChartMarkerData() {
      const hist = {
        all: {},
        terrestrial: {},
        aquatic: {},
        host: {},
        engineered: {},
      };
      this.biosamples.forEach((sample) => {
        if (sample.latitude === undefined || sample.longitude === undefined) {
          return;
        }
        const latLon = `${sample.latitude}:${sample.longitude}`;
        if (hist.all[latLon] === undefined) {
          hist.all[latLon] = 0;
        }
        hist.all[latLon] += 1;
        if (sample.ecosystem === 'Engineered') {
          if (hist.engineered[latLon] === undefined) {
            hist.engineered[latLon] = 0;
          }
          hist.engineered[latLon] += 1;
        }
        if (sample.ecosystem === 'Host-associated') {
          if (hist.host[latLon] === undefined) {
            hist.host[latLon] = 0;
          }
          hist.host[latLon] += 1;
        }
        if (sample.ecosystem_category === 'Terrestrial') {
          if (hist.terrestrial[latLon] === undefined) {
            hist.terrestrial[latLon] = 0;
          }
          hist.terrestrial[latLon] += 1;
        }
        if (sample.ecosystem_category === 'Aquatic') {
          if (hist.aquatic[latLon] === undefined) {
            hist.aquatic[latLon] = 0;
          }
          hist.aquatic[latLon] += 1;
        }
      });
      return {
        all: [
          ['Latitude', 'Longitude', 'Samples'],
          ...Object.keys(hist.all).map((latLon) => [...latLon.split(':').map((d) => +d), hist.all[latLon]]),
        ],
        host: [
          ['Latitude', 'Longitude', 'Samples'],
          ...Object.keys(hist.host).map((latLon) => [...latLon.split(':').map((d) => +d), hist.host[latLon]]),
        ],
        engineered: [
          ['Latitude', 'Longitude', 'Samples'],
          ...Object.keys(hist.engineered).map((latLon) => [...latLon.split(':').map((d) => +d), hist.engineered[latLon]]),
        ],
        terrestrial: [
          ['Latitude', 'Longitude', 'Samples'],
          ...Object.keys(hist.terrestrial).map((latLon) => [...latLon.split(':').map((d) => +d), hist.terrestrial[latLon]]),
        ],
        aquatic: [
          ['Latitude', 'Longitude', 'Samples'],
          ...Object.keys(hist.aquatic).map((latLon) => [...latLon.split(':').map((d) => +d), hist.aquatic[latLon]]),
        ],
      };
    },
    geoChartOptions() {
      return {
        all: {
          colorAxis: { colors: ['#dddddd', vuetifyColor.purple] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        host: {
          colorAxis: { colors: ['#dddddd', vuetifyColor.red] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        terrestrial: {
          colorAxis: { colors: ['#dddddd', vuetifyColor.green] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        aquatic: {
          colorAxis: { colors: ['#dddddd', vuetifyColor.blue] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        engineered: {
          colorAxis: { colors: ['#dddddd', vuetifyColor.orange] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
      };
    },
    geoChartMarkerOptions() {
      return {
        all: {
          displayMode: 'markers',
          colorAxis: { colors: [vuetifyColor.purple, vuetifyColor.purple] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        host: {
          displayMode: 'markers',
          colorAxis: { colors: [vuetifyColor.red, vuetifyColor.red] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        terrestrial: {
          displayMode: 'markers',
          colorAxis: { colors: [vuetifyColor.green, vuetifyColor.green] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        aquatic: {
          displayMode: 'markers',
          colorAxis: { colors: [vuetifyColor.blue, vuetifyColor.blue] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
        engineered: {
          displayMode: 'markers',
          colorAxis: { colors: [vuetifyColor.orange, vuetifyColor.orange] },
          backgroundColor: '#81d4fa',
          datalessRegionColor: '#eeeeee',
          defaultColor: '#f5f5f5',
        },
      };
    },
    sankeyData() {
      const hist = {};
      this.biosamples.forEach((sample) => {
        if (sample.ecosystem_category === 'Unclassified' || sample.ecosystem_category === '') {
          return;
        }
        const habitat = [
          sample.ecosystem,
          `.${sample.ecosystem_category}`,
        ].join(':');
        if (hist[habitat] === undefined) {
          hist[habitat] = 0;
        }
        hist[habitat] += 1;
      });
      // this.biosamples.forEach((sample) => {
      //   if (sample.ecosystem_type === 'Unclassified' || sample.ecosystem_type === '') {
      //     return;
      //   }
      //   const habitat = [
      //     `.${sample.ecosystem_category}`,
      //     `..${sample.ecosystem_type}`,
      //   ].join(':');
      //   if (hist[habitat] === undefined) {
      //     hist[habitat] = 0;
      //   }
      //   hist[habitat] += 1;
      // });
      // this.biosamples.forEach((sample) => {
      //   if (sample.ecosystem_subtype === 'Unclassified' || sample.ecosystem_subtype === '') {
      //     return;
      //   }
      //   const habitat = [
      //     `..${sample.ecosystem_type}`,
      //     `...${sample.ecosystem_subtype}`,
      //   ].join(':');
      //   if (hist[habitat] === undefined) {
      //     hist[habitat] = 0;
      //   }
      //   hist[habitat] += 1;
      // });
      // this.biosamples.forEach((sample) => {
      //   if (sample.specific_ecosystem === 'Unclassified' || sample.specific_ecosystem === '') {
      //     return;
      //   }
      //   const habitat = [
      //     `...${sample.ecosystem_subtype}`,
      //     `....${sample.specific_ecosystem}`,
      //   ].join(':');
      //   if (hist[habitat] === undefined) {
      //     hist[habitat] = 0;
      //   }
      //   hist[habitat] += 1;
      // });
      return [
        ['From', 'To', 'Samples'],
        ...Object.keys(hist).map((habitat) => [...habitat.split(':'), hist[habitat]]),
      ];
    },
    sankeyOptions() {
      return {
        height: 800,
        sankey: { link: { colorMode: 'source' } },
      };
    },
  },
};
</script>
