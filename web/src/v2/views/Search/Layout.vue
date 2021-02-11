<script lang="ts">
import {
  defineComponent, reactive, computed,
} from '@vue/composition-api';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
import { fieldDisplayName } from '@/util';
import { api } from '@/data/api';

import { stateRefs, toggleConditions } from '@/v2/store';
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
      stateRefs.conditions.value
        .filter((c) => c.table === 'study' && c.field === 'study_id')
        .map((c) => c.value)
    ));
    function setChecked(studyId: string) {
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
    const biosample = usePaginatedResults(stateRefs.conditions, api.searchBiosample);

    const studyType = types.study;
    const study = usePaginatedResults(stateRefs.conditions, api.searchStudy, 3);

    const loggedInUser = computed(() => typeof stateRefs.user.value === 'string');

    return {
      /* data */
      biosampleType,
      biosample,
      expandedOmicsDetails,
      loggedInUser,
      studyType,
      study,
      studyCheckboxState,
      types,
      /* methods */
      setChecked,
      setExpanded,
      fieldDisplayName,
    };
  },
});
</script>

<template>
  <div>
    <sidebar :results-count="biosample.data.results.count" />
    <v-main>
      <v-progress-linear
        v-show="biosample.data.loading || study.data.loading"
        indeterminate
        background-opacity="0"
        style="position: fixed; top: 64; z-index: 20;"
      />
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
                :loading="study.data.loading"
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
                <template #item-content="props">
                  <div>
                    <template
                      v-for="item in props.result.omics_counts"
                    >
                      <v-chip
                        v-if="item.count"
                        :key="item.type"
                        small
                        class="mr-2 my-1"
                      >
                        {{ fieldDisplayName(item.type) }}: {{ item.count }}
                      </v-chip>
                    </template>
                  </div>
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
                :loading="biosample.data.loading"
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
                      loggedInUser,
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
