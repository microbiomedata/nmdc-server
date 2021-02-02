<script lang="ts">
import {
  defineComponent, reactive, computed,
} from '@vue/composition-api';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
import { api } from '@/data/api';

import { conditions, toggleConditions } from '@/v2/store';
import usePaginatedResults from '@/v2/use/usePaginatedResults';
import SampleListExpansion from '@/v2/components/SampleListExpansion.vue';

import BiosampleVisGroup from './BiosampleVisGroup.vue';
import Sidebar from './Sidebar.vue';

export default defineComponent({
  name: 'LayoutV2',

  components: {
    BiosampleVisGroup,
    SampleListExpansion,
    SearchResults,
    Sidebar,
  },

  setup() {
    /**
     * Study checkbox state logic
     */
    const studyCheckboxState = computed(() => (
      conditions.value
        .filter((c) => c.table === 'study' && c.field === 'study_id')
        .map((c) => c.value)
    ));
    function setChecked(studyId) {
      toggleConditions([{
        value: studyId,
        table: 'study',
        op: '==',
        field: 'study_id',
      }]);
    }

    /**
     * Expanded Omics details
     */
    const expandedOmicsDetails = reactive({
      resultId: '',
      projectId: '',
    });
    function setExpanded(resultId: string, projectId: string) {
      if (expandedOmicsDetails.resultId !== resultId
        || expandedOmicsDetails.projectId !== projectId) {
        expandedOmicsDetails.resultId = resultId;
        expandedOmicsDetails.projectId = projectId;
      } else {
        expandedOmicsDetails.resultId = '';
        expandedOmicsDetails.projectId = '';
      }
    }

    const biosampleType = types.biosample;
    const biosample = usePaginatedResults(conditions, api.searchBiosample);

    const studyType = types.study;
    const study = usePaginatedResults(conditions, api.searchStudy, 3);

    return {
      /* data */
      expandedOmicsDetails,
      biosampleType,
      biosample,
      conditions,
      studyType,
      study,
      studyCheckboxState,
      /* methods */
      setChecked,
      setExpanded,
    };
  },
});
</script>

<template>
  <div>
    <sidebar :results-count="biosample.data.results.count" />
    <v-main>
      <v-container
        fluid
        class="py-0"
      >
        <v-row>
          <v-col>
            <BiosampleVisGroup />
            <v-card outlined>
              <v-card-title class="pb-0">
                Studies
              </v-card-title>
              <SearchResults
                disable-pagination
                disable-navigate-on-click
                :count="study.data.results.count"
                :icon="studyType.icon"
                :items-per-page="study.data.limit"
                :results="study.data.results.results"
                :page="study.data.pageSync"
                @set-page="study.setPage($event)"
                @selected="$router.push({ name: 'V2Sample'})"
              >
                <template #action="{ result }">
                  <v-list-item-action>
                    <v-checkbox
                      :input-value="studyCheckboxState"
                      :value="result.id"
                      @change="setChecked(result.id)"
                    />
                  </v-list-item-action>
                </template>
              </SearchResults>
            </v-card>
            <v-card
              outlined
              class="my-4"
            >
              <v-card-title class="pb-0">
                Samples
              </v-card-title>
              <SearchResults
                disable-navigate-on-click
                :count="biosample.data.results.count"
                :icon="biosampleType.icon"
                :items-per-page="biosample.data.limit"
                :results="biosample.data.results.results"
                :page="biosample.data.pageSync"
                :subtitle-key="'study_id'"
                @set-page="biosample.setPage($event)"
                @selected="$router.push({ name: 'V2Sample', params: { id: $event }})"
              >
                <template #subtitle="props">
                  Study ID: {{ props.result.study_id }}
                </template>
                <template #item-content="props">
                  <SampleListExpansion
                    v-bind="{
                      result: props.result,
                      expanded: expandedOmicsDetails,
                    }"
                    @open-details="setExpanded(props.result.id, $event)"
                  />
                </template>
              </SearchResults>
              <h2 v-if="biosample.data.results.count === 0">
                No results for selected conditions in sample table
              </h2>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </div>
</template>
