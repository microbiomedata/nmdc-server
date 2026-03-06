<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue';
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
  toggleConditions, setUniqueCondition,
} from '@/store';
import { api, Condition, FacetSummaryResponse } from '@/data/api';
import { makeSetsFromBitmask } from '@/encoding';

const helpBarchart = 'Displays the number of omics processing runs for each data type available. Click on a bar to filter by data type.';
const helpMap = `
  Shows the geographic locations (latitude and longitude) where samples were collected.
  <ul>
    <li>Click on a cluster to zoom in.</li>
    <li>Click "Search this region" to filter results to the current map view.</li>
  </ul>
  <strong>Note:</strong> Samples collected at the poles may not appear on the map due to projection limits,
  but they are included in other visualizations and the biosample table.
`;
const helpTimeline = 'Displays sample collections grouped by collection date. Click and drag on the timeline to filter by collection date. The selected region can be moved by dragging it from the center. The region can be resized by clicking and dragging at the edges. Click outside the region to clear it.';
const helpUpset = 'This UpSet plot shows the number of samples with corresponding omic data associated. For example: a sample could have metagenomics, metatranscriptomics, and natural organic matter characterizations. You can select samples by clicking on the bar chart or counts to the right of the bar chart';

const staticUpsetTooltips = {
  MG: 'Metagenomics',
  MP: 'Metaproteomics',
  MB: 'Metabolomics',
  MT: 'Metatranscriptomics',
  NOM: 'Natural Organic Matter',
  LIP: 'Lipidomics',
  AMP: 'Amplicon',
};

const props = withDefaults(defineProps<{
  conditions: Condition[];
  vistab?: number | null;
}>(), {
  vistab: null,
});

const sampleFacetSummary = ref<FacetSummaryResponse[] | null>(null);
const studyFacetSummary = ref<FacetSummaryResponse[] | null>(null);
const isUpsetLoading = ref(true);

const upsetData = computed(() => {
  const multiomicsObj: Record<string, { counts: any, sets: any }> = {};
  if (sampleFacetSummary.value) {
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
  }
  if (studyFacetSummary.value) {
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
  }
  return Object.keys(multiomicsObj)
    .sort((a, b) => parseInt(a, 10) - parseInt(b, 10))
    .map((k) => multiomicsObj[k]);
});

const upsetErrorMessage = computed(() => {
  if (sampleFacetSummary.value === null) {
    return 'Could not retrieve sample summary values for UpSet plot';
  } else if (studyFacetSummary.value === null) {
    return 'Could not retrieve study summary values for UpSet plot';
  }
  return null;
});

watchEffect(async () => {
  try {
    isUpsetLoading.value = true;
    [sampleFacetSummary.value, studyFacetSummary.value] = await Promise.all([
      api.getFacetSummary('biosample', 'multiomics', props.conditions),
      api.getFacetSummary('study', 'multiomics', props.conditions),
    ]);
  } catch (error) {
    console.error('Error fetching facet summaries for UpSet plot:', error);
    sampleFacetSummary.value = null;
    studyFacetSummary.value = null;
  } finally {
    isUpsetLoading.value = false;
  }
});

function setBoundsFromMap(val: Condition[]) {
  setUniqueCondition(['latitude', 'longitude'], ['biosample'], val);
}
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
      <v-col
        class="pl-0"
        :cols="7"
      >
        <TooltipCard
          :text="helpMap"
          class="pa-1"
        >
          <ClusterMap
            :conditions="conditions"
            :height="360"
            :vistab="vistab"
            @selected="setBoundsFromMap($event)"
          />
        </TooltipCard>
      </v-col>
    </v-row>
    <v-row class="mt-0">
      <v-col cols="6">
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
                :height="240"
                @select="setUniqueCondition(['collection_date'], ['biosample'], $event.conditions)"
              />
            </template>
          </BinnedSummaryWrapper>
        </TooltipCard>
      </v-col>
      <v-col
        class="pl-0"
        cols="6"
      >
        <TooltipCard
          :text="helpUpset"
          class="py-0 d-flex flex-column justify-center fill-height"
        >
          <div
            v-if="isUpsetLoading || upsetErrorMessage"
            class="d-flex justify-center align-center"
            style="height: 240px"
          >
            <v-progress-circular
              v-if="isUpsetLoading"
              indeterminate
              color="primary"
            />
            <div v-else>
              {{ upsetErrorMessage }}
            </div>
          </div>
          <ChartContainer
            v-else
            :height="240"
          >
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
            <span
              v-for="value, key in staticUpsetTooltips"
              :key="key"
            >
              {{ key }}: {{ value }}
            </span>
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
