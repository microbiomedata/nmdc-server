<script setup lang="ts">
import { computed, ref } from 'vue';
import { GChart } from 'vue-google-charts';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import { ecosystems } from '@/encoding';
import { Condition, FacetSummaryResponse } from '@/data/api';
import { useTheme } from 'vuetify';

const props = withDefaults(defineProps<{
  showTitle?: boolean;
  showBaseline?: boolean;
  leftMargin?: number;
  rightMargin?: number;
  chart?: string | null;
  table: string;
  field: string;
  height?: number;
  stacked?: boolean;
  facetSummary: FacetSummaryResponse[] | null;
  facetSummaryUnconditional: FacetSummaryResponse[] | null;
  errorMessage?: string | null;
}>(), {
  showTitle: true,
  showBaseline: true,
  leftMargin: 80,
  rightMargin: 40,
  chart: null,
  height: 200,
  stacked: true,
  errorMessage: null,
});

const emit = defineEmits<{
  (e: 'selected', payload: { conditions: Condition[] }): void;
}>();

const theme = useTheme();
const chartRef = ref();

const onChartReady = (chart: any) => {
  chartRef.value = chart;
};

const chartEvents = {
  select: () => {
    const selection = chartRef.value.getSelection();
    const value = !props.facetSummaryUnconditional ? null : props.facetSummaryUnconditional[selection[0].row]?.facet;
    if (value && selection.length === 1) {
      emit('selected', {
        conditions: [{
          field: props.field,
          op: '==',
          value,
          table: props.table,
        }],
      });
    }
  },
};

const chartData = computed(() => {
  let data = [
    [
      { label: fieldDisplayName(props.field) },
      { label: 'Match', role: 'data' },
      { role: 'scope' },
      { role: 'style' },
      { label: 'No Match', role: 'data' },
      { role: 'scope' },
      { role: 'style' },
      { role: 'annotation' },
    ]
  ];

  const currentFacetSummary = props.facetSummary;

  if (currentFacetSummary && props.facetSummaryUnconditional) {
    data = [
      ...data,
      ...props.facetSummaryUnconditional.map(
        (facet) => {
          const count = (currentFacetSummary.find((e) => e.facet === facet.facet) || {}).count || 0;
          const excludedCount = facet.count - ((currentFacetSummary.find(
            (e) => e.facet === facet.facet,
          ) || {}).count || 0);
          return [
            fieldDisplayName(facet.facet),
            count,
            true,
            count > 0 ? (
              ecosystems.find((e) => e.name === facet.facet)
              || { color: theme.current.value.colors.primary }
            ).color : 'lightgray',
            excludedCount,
            false,
            excludedCount > 0 ? 'lightgray' : theme.current.value.colors.primary,
            count > 0 ? `${count}` : 'No match',
          ];
        },
      ),
    ]
  }
  return data;
});

const barChartOptions = computed(() => ({
  height: props.height,
  chartArea: {
    left: props.leftMargin,
    right: props.rightMargin,
    top: 0,
    width: '85%',
    height: '100%',
  },
  hAxis: {
    textStyle: {
      fontName: 'Roboto',
    },
    gridlines: {
      count: 0,
    },
    ticks: [],
    baselineColor: props.showBaseline ? 'black' : 'transparent',
    baseline: 0,
    viewWindowMode: 'maximized',
  },
  vAxis: {
    textStyle: {
      fontName: 'Roboto',
    },
  },
  legend: { position: 'none' },
  annotations: { alwaysOutside: true, stem: { color: 'transparent' } },
  title: props.showTitle ? fieldDisplayName(props.field) : null,
  isStacked: true,
}));

const isLoading = computed(() => props.facetSummaryUnconditional == null && props.errorMessage == null);
console.log(isLoading.value);
console.log(props.errorMessage);
</script>

<template>
  <div>
    <div
      v-if="isLoading || errorMessage"
      class="d-flex justify-center align-center"
      :style="{ height: `${height}px` }"
    >
      <v-progress-circular
        v-if="isLoading"
        indeterminate
        color="primary"
      />
      <div v-else>
        {{ errorMessage }}
      </div>
    </div>
    <GChart
      v-else
      type="BarChart"
      class="rounded overflow-hidden"
      :data="chartData"
      :options="barChartOptions"
      :events="chartEvents as any"
      @ready="onChartReady"
    />
  </div>
</template>
