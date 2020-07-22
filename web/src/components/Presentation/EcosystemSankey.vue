<template>
  <GChart
    ref="chart"
    :settings="{
      packages: ['sankey'],
    }"
    type="Sankey"
    :data="sankeyData"
    :options="sankeyOptions"
    :events="chartEvents"
  />
</template>

<script>
import { GChart } from 'vue-google-charts';

import colors from '@/colors';
import { api } from '@/data/api';
import { ecosystems } from '@/encoding';

export default {
  components: {
    GChart,
  },
  props: {
    type: {
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
      ecosystems,
      chartEvents: {
        select: () => {
          const chart = this.$refs.chart.chartObject;
          const selection = chart.getSelection();
          if (selection.length === 1) {
            let val;
            if (selection[0].name) {
              val = selection[0].name;
            } else {
              [, val] = this.sankeyData[selection[0].row + 1];
            }
            let value = val;
            let field = 'ecosystem';
            if (val[0] === ' ') {
              field = 'ecosystem_category';
              value = val.substring(1);
            }
            if (val[1] === ' ') {
              field = 'ecosystem_type';
              value = val.substring(2);
            }
            if (val[2] === ' ') {
              field = 'ecosystem_subtype';
              value = val.substring(3);
            }
            if (val[3] === ' ') {
              field = 'specific_ecosystem';
              value = val.substring(4);
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
  asyncComputed: {
    async sankeyData() {
      const data = await api.getEnvironmentSankeyAggregation(this.conditions);
      const hist = {};
      data.forEach((sample) => {
        const habitat = [
          sample.ecosystem,
          ` ${sample.ecosystem_category}`,
        ].join(':');
        if (hist[habitat] === undefined) {
          hist[habitat] = 0;
        }
        hist[habitat] += sample.count;
      });
      data.forEach((sample) => {
        const habitat = [
          ` ${sample.ecosystem_category}`,
          `  ${sample.ecosystem_type}`,
        ].join(':');
        if (hist[habitat] === undefined) {
          hist[habitat] = 0;
        }
        hist[habitat] += sample.count;
      });
      data.forEach((sample) => {
        const habitat = [
          `  ${sample.ecosystem_type}`,
          `   ${sample.ecosystem_subtype}`,
        ].join(':');
        if (hist[habitat] === undefined) {
          hist[habitat] = 0;
        }
        hist[habitat] += sample.count;
      });
      data.forEach((sample) => {
        const habitat = [
          `   ${sample.ecosystem_subtype}`,
          `    ${sample.specific_ecosystem}`,
        ].join(':');
        if (hist[habitat] === undefined) {
          hist[habitat] = 0;
        }
        hist[habitat] += sample.count;
      });
      return [
        ['From', 'To', 'Samples'],
        ...Object.keys(hist).map((habitat) => [...habitat.split(':'), hist[habitat]]),
      ];
    },
  },
  computed: {
    sankeyOptions() {
      return {
        height: 300,
        sankey: {
          link: {
            colorMode: 'source',
            interactivity: true,
          },
          node: {
            interactivity: true,
            colors: colors.primary,
          },
        },
      };
    },
  },
};
</script>
