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
import Vue from 'vue';
import { GChart } from 'vue-google-charts';

import colors from '@/colors';
import { api } from '@/data/api';
import { ecosystems } from '@/encoding';
import { makeTree } from '@/util';

export default Vue.extend({
  components: {
    GChart,
  },
  props: {
    table: {
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
            conditions: [{
              field: this.heirarchy[prefix],
              op: '==',
              value: val.trim(),
              table: 'biosample',
            }],
          });
        },
      },
    };
  },
  asyncComputed: {
    async sankeyData() {
      const data = await api.getEnvironmentSankeyAggregation(this.conditions);
      const tree = makeTree(data, this.heirarchy);
      return [
        ['From', 'To', 'Samples'],
        // generate sankey data from topological sort of sankey tree
        ...tree.topoSort
          // filter root node and root's direct children
          .filter((node) => node.id !== '' && node.parent.id !== '')
          .map(({
            name, parent, count, depth,
          }) => ([
            // Add depth-dependent spacing so each level's unclassified is unique
            ' '.repeat(depth - 1) + parent.name,
            ' '.repeat(depth) + name,
            count,
          ])),
      ];
    },
  },
  computed: {
    sankeyOptions() {
      return {
        // Make the chart height dependent on the number of nodes with a minimum of 500px
        height: Math.max(this.sankeyData.length * 4, 500),
        sankey: {
          link: {
            colorMode: 'source',
            interactivity: true,
          },
          node: {
            interactivity: true,
            // Array needs to be of substantial length so the lines do not become too pale to see
            // Uses 'primary' and primary.darken2 alternatingly
            colors: Array.from({ length: this.sankeyData.length / 2 }, (_, i) => (i % 2 === 0 ? colors.primary : '#1c104e')),
          },
        },
      };
    },
  },
});
</script>
