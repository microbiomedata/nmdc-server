<script setup lang="ts">
import ChartContainer from '@/components/Presentation/ChartContainer.vue';
import DateHistogram from '@/components/Presentation/DateHistogram.vue';
import UpSet from '@/components/Presentation/UpSet.vue';
import { computed, ref, watchEffect } from 'vue';
// TODO: replace with composition functions
import BinnedSummaryWrapper from '@/components/Wrappers/BinnedSummaryWrapper.vue';
// ENDTODO
import HelpWrapper from '@/components/HelpWrapper.vue';
import LoadingOverlay from '@/components/LoadingOverlay.vue';

import { api, Condition, FacetSummaryResponse } from '@/data/api';
import { makeSetsFromBitmask } from '@/encoding';
import {
  setUniqueCondition
} from '@/store';
import useRequest from '@/use/useRequest';
import { VISUALIZATION_HEIGHT } from '@/views/Search/types';

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

const props = defineProps<{
  conditions: Condition[];
}>();

const sampleFacetSummary = ref<FacetSummaryResponse[] | null>(null);
const studyFacetSummary = ref<FacetSummaryResponse[] | null>(null);
const sampleRequest = useRequest();
const studyRequest = useRequest();
const upSetLoading = computed(() => sampleRequest.loading.value || studyRequest.loading.value);
const upSetError = computed(() => {
  if (sampleRequest.error.value) {
    return 'Could not retrieve sample summary values for UpSet plot';
  } else if (studyRequest.error.value) {
    return 'Could not retrieve study summary values for UpSet plot';
  }
  return null;
});

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

watchEffect(async () => {
  sampleFacetSummary.value = await sampleRequest.request(() => api.getFacetSummary('biosample', 'multiomics', props.conditions));
  studyFacetSummary.value = await studyRequest.request(() => api.getFacetSummary('study', 'multiomics', props.conditions));
});
</script>

<template>
  <div>
    <v-row class="mt-0">
      <v-col
        class="border-e"
        cols="6"
      >
        <HelpWrapper
          :height="VISUALIZATION_HEIGHT"
          :help-text="helpTimeline"
        >
          <BinnedSummaryWrapper
            table="biosample"
            field="collection_date"
            :conditions="conditions"
            use-all-conditions
          >
            <template #default="slotProps">
              <DateHistogram
                v-bind="slotProps"
                :height="VISUALIZATION_HEIGHT"
                @select="setUniqueCondition(['collection_date'], ['biosample'], $event.conditions)"
              />
            </template>
          </BinnedSummaryWrapper>
        </HelpWrapper>
      </v-col>
      <v-col
        class="pl-0"
        cols="6"
      >
        <HelpWrapper
          :height="VISUALIZATION_HEIGHT"
          :help-text="helpUpset"
          class="py-0 d-flex flex-column justify-center fill-height"
        >
          <LoadingOverlay
            :loading="upSetLoading"
            :error="upSetError"
            :height="VISUALIZATION_HEIGHT"
          />
          <ChartContainer
            :height="331"
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
        </HelpWrapper>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.upset-legend {
  height: 29px;
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
