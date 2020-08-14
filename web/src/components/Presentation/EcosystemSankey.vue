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

function generateLayer(data, heirarchy, depth) {
  const [from, to] = heirarchy.slice(depth, depth + 2);
  const histogram = {};
  data.forEach((item) => {
    const key = `${' '.repeat(depth + 1)}${item[from]}:${' '.repeat(depth + 2)}${item[to]}`;
    histogram[key] = (histogram[key] || 0) + item.count;
  });
  return Object.entries(histogram)
    .map(([key, value]) => [...key.split(':'), value]);
}

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
    heirarchy: {
      type: Array,
      default: () => ['ecosystem', 'ecosystem_category', 'ecosystem_type', 'ecosystem_subtype', 'specific_ecosystem'],
    },
  },
  data() {
    return {
      ecosystems,
      chartEvents: {
        select: () => {
          const chart = this.$refs.chart.chartObject;
          const selection = chart.getSelection();
          if (selection.length === 0) return;
          const [, val] = this.sankeyData[selection[0].row + 1];
          // use prefixed number of spaces to indicate index in the heirarchy
          const prefix = val.match(/^([\s]+)/g)[0].length - 1;
          this.$emit('selected', {
            type: this.type,
            conditions: [{
              field: this.heirarchy[prefix],
              op: '==',
              value: val.trim(),
              table: this.type,
            }],
          });
        },
      },
    };
  },
  asyncComputed: {
    async sankeyData() {
      const data = await api.getEnvironmentSankeyAggregation(this.conditions);
      return [
        ['From', 'To', 'Samples'],
        ...generateLayer(data, this.heirarchy, 0),
        ...generateLayer(data, this.heirarchy, 1),
        ...generateLayer(data, this.heirarchy, 2),
        ...generateLayer(data, this.heirarchy, 3),
      ];
    },
  },
  computed: {
    sankeyOptions() {
      return {
        height: 500,
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
