<script lang="ts">
import { defineComponent } from '@vue/composition-api';
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

import {
  stateRefs, toggleConditions, removeConditions, setUniqueCondition,
} from '@/v2/store';

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
    sets: ['OM', 'MT', 'MG'],
    counts: { Samples: 43, Studies: 1 },
  },
  {
    sets: ['MG', 'MT'],
    counts: { Samples: 2, Studies: 1 },
  },
  {
    sets: ['OM', 'MG'],
    counts: { Samples: 3, Studies: 1 },
  },
  {
    sets: ['MP', 'MB'],
    counts: { Samples: 1, Studies: 1 },
  },
  {
    sets: ['OM'],
    counts: { Samples: 34, Studies: 1 },
  },
];
const staticUpsetTooltips = {
  MG: 'Metagenomics',
  MP: 'Metaproteomics',
  MB: 'Metabolomics',
  MT: 'Metatranscriptomics',
  OM: 'Organic Matter',
};

export default defineComponent({
  name: 'SampleVisGroupV2',
  components: {
    ChartContainer,
    DateHistogram,
    FacetBarChart,
    LocationMap,
    EcosystemSankey,
    // TODO replace with composition functions
    FacetSummaryWrapper,
    BinnedSummaryWrapper,
    UpSet,
  },
  setup() {
    return {
      conditions: stateRefs.conditions,
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
        <v-card
          outlined
          class="pa-1"
        >
          <FacetSummaryWrapper
            table="project"
            field="omics_type"
            :conditions="conditions"
            use-all-conditions
          >
            <template #default="props">
              <FacetBarChart
                v-bind="props"
                :height="400"
                :show-title="false"
                :show-baseline="false"
                :left-margin="120"
                :right-margin="80"
                @selected="toggleConditions($event.conditions)"
              />
            </template>
          </FacetSummaryWrapper>
        </v-card>
      </v-col>
      <v-col :cols="8">
        <v-card
          outlined
          class="pa-1"
        >
          <LocationMap
            type="biosample"
            :conditions="conditions"
            @selected="toggleConditions($event.conditions)"
          />
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="8">
        <v-card
          outlined
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
        </v-card>
      </v-col>
      <v-col cols="4">
        <v-card
          outlined
          height="100%"
          class="py-0 d-flex flex-column justify-center"
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
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
