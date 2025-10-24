<script lang="ts">
import {
  computed, defineComponent, PropType, ref,
} from 'vue';
import { GChart } from 'vue-google-charts';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import { ecosystems } from '@/encoding';
import { FacetSummaryResponse } from '@/data/api';
import { useTheme } from 'vuetify';
import { GoogleVizEvents } from 'vue-google-charts/dist/types';

export default defineComponent({
  name: 'FacetBarChart',
  components: {
    GChart,
  },
  props: {
    showTitle: {
      type: Boolean,
      default: true,
    },
    showBaseline: {
      type: Boolean,
      default: true,
    },
    leftMargin: {
      type: Number,
      default: 80,
    },
    rightMargin: {
      type: Number,
      default: 40,
    },
    chart: {
      type: String,
      default: null,
    },
    table: {
      type: String,
      default: null,
    },
    field: {
      type: String,
      default: null,
    },
    height: {
      type: Number,
      default: 200,
    },
    stacked: {
      type: Boolean,
      default: true,
    },
    facetSummary: {
      type: Array as PropType<FacetSummaryResponse[]>,
      required: true,
    },
    facetSummaryUnconditional: {
      type: Array as PropType<FacetSummaryResponse[]>,
      required: true,
    },
  },

  setup(props, { emit }) {
    const theme = useTheme();
    const chartRef = ref();

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const onChartReady = (chart: any) => {
      chartRef.value = chart;
    };
    const chartEvents = {
      select: () => {
        const selection = chartRef.value.getSelection();
        const value = props.facetSummaryUnconditional[selection[0].row]?.facet;
        if (selection.length === 1) {
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
      console.log('FacetBarChart chartData recomputed:', {
        facetSummaryLength: props.facetSummary.length,
        facetSummaryUnconditionalLength: props.facetSummaryUnconditional.length,
        field: props.field
      });
      return [
        [
          { label: fieldDisplayName(props.field) },
          { label: 'Match', role: 'data' },
          { role: 'scope' },
          { role: 'style' },
          { label: 'No Match', role: 'data' },
          { role: 'scope' },
          { role: 'style' },
          { role: 'annotation' },
        ],
      ...props.facetSummaryUnconditional.map(
        (facet) => {
          const count = (props.facetSummary.find((e) => e.facet === facet.facet) || {}).count || 0;
          const excludedCount = facet.count - ((props.facetSummary.find(
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
    ];
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

    return {
      chartRef,
      onChartReady,
      chartEvents,
      chartData,
      barChartOptions,
    };
  },
});
</script>

<template>
  <GChart
    type="BarChart"
    class="rounded overflow-hidden"
    :data="chartData"
    :options="barChartOptions"
    :events="chartEvents as any"
    @ready="onChartReady"
  />
</template>
