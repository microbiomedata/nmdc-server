<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
import FacetBarChart from '@/components/Presentation/FacetBarChart.vue';
import DateHistogram from '@/components/Presentation/DateHistogram.vue';
import LocationMap from '@/components/Presentation/LocationMap.vue';
import UpSet from '@/components/Presentation/UpSet.vue';
import ChartContainer from '@/components/Presentation/ChartContainer.vue';
// TODO: replace with composition functions
import FacetSummaryWrapper from '@/components/FacetSummaryWrapper.vue';
import BinnedSummaryWrapper from '@/components/BinnedSummaryWrapper.vue';
// ENDTODO
import TooltipCard from '@/v2/components/TooltipCard.vue';

import {
  toggleConditions, removeConditions, setUniqueCondition,
} from '@/v2/store';
import { Condition } from '@/data/api';

const helpBarchart = 'Displays the number of samples for each data type available. Click on a bar to filter by data type.';
const helpMap = 'Displays geographical location (latitude, longitude) and sample size (as indicated by the size of the point). Click on a point to filter by a group of samples.';
const helpTimeline = 'Scroll the slider to narrow in on a sample collection date range.';
const helpUpset = 'This upset plot shows the number of samples with corresponding omic data associated. For example: there are 43 samples from 1 study that have metagenomics, metatranscriptomics, and natural organic matter characterizations.';

const staticUpsetData = [
  {
    sets: ['MG'],
    counts: { Samples: 42, Studies: 2 },
  },
  {
    sets: ['MG', 'MP', 'MB'],
    counts: { Samples: 33, Studies: 1 },
  },
  {
    sets: ['NOM', 'MT', 'MG'],
    counts: { Samples: 43, Studies: 1 },
  },
  {
    sets: ['MG', 'MT'],
    counts: { Samples: 2, Studies: 1 },
  },
  {
    sets: ['NOM', 'MG'],
    counts: { Samples: 3, Studies: 1 },
  },
  {
    sets: ['MP', 'MB'],
    counts: { Samples: 1, Studies: 1 },
  },
  {
    sets: ['NOM'],
    counts: { Samples: 34, Studies: 1 },
  },
];
const staticUpsetTooltips = {
  MG: 'Metagenomics',
  MP: 'Metaproteomics',
  MB: 'Metabolomics',
  MT: 'Metatranscriptomics',
  NOM: 'Natural Organic Matter',
};

export default defineComponent({
  name: 'SampleVisGroupV2',
  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },
  components: {
    ChartContainer,
    DateHistogram,
    FacetBarChart,
    LocationMap,
    EcosystemSankey,
    TooltipCard,
    // TODO replace with composition functions
    FacetSummaryWrapper,
    BinnedSummaryWrapper,
    UpSet,
  },
  setup() {
    return {
      helpBarchart,
      helpMap,
      helpTimeline,
      helpUpset,
      toggleConditions,
      setUniqueCondition,
      removeConditions,
      staticUpsetData,
      staticUpsetTooltips,
    };
  },
});
</script>

<template>
  <div>
    <v-row>
      <v-col :cols="4">
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
      <v-col :cols="8">
        <TooltipCard
          :text="helpMap"
          class="pa-1"
        >
          <LocationMap
            type="biosample"
            :conditions="conditions"
            @selected="toggleConditions($event.conditions)"
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
                @select="setUniqueCondition('collection_date', 'biosample', $event.conditions)"
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
                  data: staticUpsetData,
                  tooltips: staticUpsetTooltips,
                  order: 'Samples'
                }"
              />
            </template>
          </ChartContainer>
        </TooltipCard>
      </v-col>
    </v-row>
  </div>
</template>
