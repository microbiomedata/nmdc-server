<script lang="ts">
import {
  computed, defineComponent, ref, watchEffect, PropType,
} from '@vue/composition-api';
import FacetBarChart from '@/components/Presentation/FacetBarChart.vue';
import DateHistogram from '@/components/Presentation/DateHistogram.vue';

import UpSet from '@/components/Presentation/UpSet.vue';
import ChartContainer from '@/components/Presentation/ChartContainer.vue';
// TODO: replace with composition functions
import FacetSummaryWrapper from '@/components/Wrappers/FacetSummaryWrapper.vue';
import BinnedSummaryWrapper from '@/components/Wrappers/BinnedSummaryWrapper.vue';
// ENDTODO
import TooltipCard from '@/components/TooltipCard.vue';
import ClusterMap from '@/components/ClusterMap.vue';

import {
  toggleConditions, removeConditions, setUniqueCondition,
} from '@/store';
import { api, Condition, FacetSummaryResponse } from '@/data/api';
import { makeSetsFromBitmask } from '@/encoding';

const helpBarchart = 'Displays the number of omics processing runs for each data type available. Click on a bar to filter by data type.';
const helpMap = 'Displays geographical location (latitude, longitude) of sample collection sites. Click on a cluster to zoom in.  Click "Search this regon" to limit search to the current map bounds.';
const helpTimeline = 'Displays sample collections grouped by collection date. Click and drag on the timeline to filter by collection date. The selected region can be moved by dragging it from the center. The region can be resized by clicking and dragging at the edges. Click outside the region to clear it.';
const helpUpset = 'This upset plot shows the number of samples with corresponding omic data associated. For example: there are 43 samples from 1 study that have metagenomics, metatranscriptomics, and natural organic matter characterizations.';

const staticUpsetTooltips = {
  MG: 'Metagenomics',
  MP: 'Metaproteomics',
  MB: 'Metabolomics',
  MT: 'Metatranscriptomics',
  NOM: 'Natural Organic Matter',
  LIP: 'Lipidomics',
};

export default defineComponent({
  name: 'SampleVisGroup',

  components: {
    ChartContainer,
    DateHistogram,
    FacetBarChart,
    ClusterMap,
    TooltipCard,
    // TODO replace with composition functions
    FacetSummaryWrapper,
    BinnedSummaryWrapper,
    UpSet,
  },

  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },

  setup(props) {
    const sampleFacetSummary = ref([] as FacetSummaryResponse[]);
    const studyFacetSummary = ref([] as FacetSummaryResponse[]);

    const upsetData = computed(() => {
      const multiomicsObj: Record<string, { counts: any, sets: any }> = {};
      sampleFacetSummary.value.forEach(({ facet, count }) => {
        if (parseInt(facet, 10) === 0) {
          return;
        }
        multiomicsObj[facet] = {
          counts: {
            Samples: count,
            Studies: 0,
          },
          sets: makeSetsFromBitmask(facet),
        };
      });
      studyFacetSummary.value.forEach(({ facet, count }) => {
        if (parseInt(facet, 10) === 0) {
          return;
        }
        if (!multiomicsObj[facet]) {
          multiomicsObj[facet] = {
            counts: {
              Samples: 0,
            },
            sets: makeSetsFromBitmask(facet),
          };
        }
        multiomicsObj[facet].counts.Studies = count;
      });
      return Object.keys(multiomicsObj)
        .sort((a, b) => parseInt(a, 10) - parseInt(b, 10))
        .map((k) => multiomicsObj[k]);
    });

    watchEffect(async () => {
      sampleFacetSummary.value = await api.getFacetSummary(
        'biosample',
        'multiomics',
        props.conditions,
      );
      studyFacetSummary.value = await api.getFacetSummary(
        'study',
        'multiomics',
        props.conditions,
      );
    });

    function setBoundsFromMap(val: Condition[]) {
      setUniqueCondition(['latitude', 'longitude'], ['biosample'], val);
    }

    return {
      helpBarchart,
      helpMap,
      helpTimeline,
      helpUpset,
      toggleConditions,
      setUniqueCondition,
      removeConditions,
      setBoundsFromMap,
      staticUpsetTooltips,
      upsetData,
    };
  },
});
</script>

<template>
  <div>
    <v-row>
      <v-col :cols="5">
        <TooltipCard :text="helpBarchart">
          <FacetSummaryWrapper
            table="omics_processing"
            field="omics_type"
            :conditions="conditions"
            use-all-conditions
          >
            <template #default="props">
              <FacetBarChart
                v-bind="props"
                :height="360"
                :show-title="false"
                :show-baseline="false"
                :left-margin="120"
                :right-margin="80"
                @selected="toggleConditions($event.conditions)"
              />
            </template>
          </FacetSummaryWrapper>
        </TooltipCard>
      </v-col>
      <v-col :cols="7">
        <TooltipCard
          :text="helpMap"
          class="pa-1"
        >
          <ClusterMap
            :conditions="conditions"
            :height="360"
            @selected="setBoundsFromMap($event)"
          />
        </TooltipCard>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="8">
        <TooltipCard
          :text="helpTimeline"
          class="py-2"
        >
          <BinnedSummaryWrapper
            table="biosample"
            field="collection_date"
            :conditions="conditions"
            use-all-conditions
          >
            <template #default="props">
              <DateHistogram
                v-bind="props"
                @select="setUniqueCondition(['collection_date'], ['biosample'], $event.conditions)"
              />
            </template>
          </BinnedSummaryWrapper>
        </TooltipCard>
      </v-col>
      <v-col cols="4">
        <TooltipCard
          :text="helpUpset"
          class="py-0 d-flex flex-column justify-center fill-height"
        >
          <ChartContainer :height="160">
            <template #default="{ width, height }">
              <UpSet
                v-bind="{
                  width,
                  height,
                  data: upsetData,
                  tooltips: staticUpsetTooltips,
                  order: 'Samples',
                }"
                @select="setUniqueCondition(
                  ['omics_type'], ['omics_processing'], $event.conditions)"
              />
            </template>
          </ChartContainer>
          <div class="mx-5 upset-legend">
            <span>MG: metagenomics</span>
            <span>MT: metatranscriptomics</span>
            <span>MP: metaproteomics</span>
            <span>MB: metabolomics</span>
            <span>NOM: natural organic matter</span>
            <span>LI: Lipidomics</span>
          </div>
        </TooltipCard>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.upset-legend {
  display: flex;
  flex-wrap: wrap;
  line-height: 0.9em;
}
.upset-legend > span {
  font-size: 10px;
  padding: 0 4px;
  white-space: nowrap;
}
</style>
