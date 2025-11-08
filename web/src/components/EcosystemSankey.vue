<script setup lang="ts">
import { ref, computed } from 'vue';
import { GChart } from 'vue-google-charts';
import { computedAsync } from '@vueuse/core';
// @ts-ignore
import colors from '@/colors';
import { api, type Condition } from '@/data/api';
// @ts-ignore
import { makeTree } from '@/util';

export interface EcosystemSankeyProps {
  conditions?: Condition[];
  hierarchy?: string[];
}

const { 
  conditions = [], 
  hierarchy = ['ecosystem', 'ecosystem_category', 'ecosystem_type', 'ecosystem_subtype', 'specific_ecosystem'] 
} = defineProps<EcosystemSankeyProps>();

const emit = defineEmits(['selected']);

const chartRef = ref();

 
const onChartReady = (chart: any) => {
  chartRef.value = chart;
};

const sankeyData = computedAsync(
  async () => {
    const data = await api.getEnvironmentSankeyAggregation(conditions);
    const tree = makeTree(data, hierarchy);
    return [
      ['From', 'To', 'Samples'],
      // generate sankey data from topological sort of sankey tree
      ...tree.topoSort
        // filter root node and root's direct children
        .filter((node: any) => node.id !== '' && node.parent.id !== '')
        .map(({
          name, parent, count, depth,
        }: any) => ([
          // Add depth-dependent spacing so each level's unclassified is unique
          ' '.repeat(depth - 1) + parent.name,
          ' '.repeat(depth) + name,
          count,
        ])),
    ];
  },
  [['From', 'To', 'Samples']], // Default value while loading
);

const chartEvents = {
  select: () => {
    const selection = chartRef.value?.getSelection();
    if (selection.length === 0) return;
    
    let val = '';
    // Handle case where the selection is a node (not a link)
    if (selection[0].row === undefined) {
      val = selection[0].name;
    } else {
      [, val] = sankeyData.value[selection[0].row + 1];
    }
    
    // use prefixed number of spaces to indicate index in the hierarchy
    const match = val.match(/^([\s]+)/g);
    if (!match) return;
    const prefix = match[0].length - 1;
    emit('selected', {
      conditions: [{
        field: hierarchy[prefix],
        op: '==',
        value: val.trim(),
        table: 'biosample',
      }],
    });
  },
};

const sankeyOptions = computed(() => {
  // Guard against undefined sankeyData (async computed property)
  const dataLength = sankeyData.value?.length || 0;
  return {
    // Make the chart height dependent on the number of nodes with a minimum of 500px
    height: Math.max(dataLength * 4, 500),
    sankey: {
      link: {
        colorMode: 'source',
        interactivity: true,
      },
      node: {
        interactivity: true,
        width: 12,
        // Array needs to be of substantial length so the lines do not become too pale to see
        // Uses 'primary' and primary.darken2 alternatingly
        colors: Array.from({ length: dataLength / 2 }, (_, i) => (i % 2 === 0 ? colors.primary : '#1c104e')),
      },
    },
  };
});
</script>

<template>
  <GChart
    ref="chart"
    :settings="{
      packages: ['sankey'],
    }"
    type="Sankey"
    :data="sankeyData"
    :options="sankeyOptions"
    :events="chartEvents as any"
    @ready="onChartReady"
  />
</template>