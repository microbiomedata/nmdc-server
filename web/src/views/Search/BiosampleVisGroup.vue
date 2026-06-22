<script setup lang="ts">
import { ref, watchEffect } from 'vue';
import FacetBarChart from '@/components/Presentation/FacetBarChart.vue';
// TODO: replace with composition functions
import FacetSummaryWrapper from '@/components/Wrappers/FacetSummaryWrapper.vue';
// ENDTODO
import HelpWrapper from '@/components/HelpWrapper.vue';
import ClusterMap from '@/components/ClusterMap.vue';

import {
  toggleConditions, setUniqueCondition,
} from '@/store';
import { api, Condition, FacetSummaryResponse } from '@/data/api';
import useRequest from '@/use/useRequest';

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

const props = withDefaults(defineProps<{
  conditions: Condition[];
  visTab?: string | null;
}>(), {
  visTab: null,
});

const sampleFacetSummary = ref<FacetSummaryResponse[] | null>(null);
const studyFacetSummary = ref<FacetSummaryResponse[] | null>(null);
const sampleRequest = useRequest();
const studyRequest = useRequest();

watchEffect(async () => {
  sampleFacetSummary.value = await sampleRequest.request(() => api.getFacetSummary('biosample', 'multiomics', props.conditions));
  studyFacetSummary.value = await studyRequest.request(() => api.getFacetSummary('study', 'multiomics', props.conditions));
});

function setBoundsFromMap(val: Condition[]) {
  setUniqueCondition(['latitude', 'longitude'], ['biosample'], val);
}
</script>

<template>
  <div>
    <v-row>
      <v-col
        class="border-e"
        :cols="5"
      >
        <HelpWrapper :help-text="helpBarchart">
          <FacetSummaryWrapper
            table="omics_processing"
            field="omics_type"
            :conditions="conditions"
            use-all-conditions
          >
            <template #default="slotProps">
              <FacetBarChart
                v-bind="slotProps"
                :height="360"
                :show-title="false"
                :show-baseline="false"
                :left-margin="120"
                :right-margin="80"
                @selected="toggleConditions($event.conditions)"
              />
            </template>
          </FacetSummaryWrapper>
        </HelpWrapper>
      </v-col>
      <v-col
        class="pl-0"
        :cols="7"
      >
        <HelpWrapper
          :help-text="helpMap"
          :height="360"
          allow-fullscreen
        >
          <template #default="{ isFullscreen }">
            <ClusterMap
              :conditions="conditions"
              :height="isFullscreen ? '90vh' : 360"
              :vis-tab="visTab"
              @selected="setBoundsFromMap($event)"
            />
          </template>
        </HelpWrapper>
      </v-col>
    </v-row>
  </div>
</template>
