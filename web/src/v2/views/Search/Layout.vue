<script lang="ts">
import {
  defineComponent, reactive, computed, ref,
} from '@vue/composition-api';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
import { fieldDisplayName } from '@/util';
import { api } from '@/data/api';

import { stateRefs, toggleConditions } from '@/v2/store';
import useFacetSummaryData from '@/v2/use/useFacetSummaryData';
import usePaginatedResults from '@/v2/use/usePaginatedResults';
import useClockGate from '@/v2/use/useClockGate';
import SampleListExpansion from '@/v2/components/SampleListExpansion.vue';

import EnvironmentVisGroup from './EnvironmentVisGroup.vue';
import BiosampleVisGroup from './BiosampleVisGroup.vue';
import Sidebar from './Sidebar.vue';

export default defineComponent({
  name: 'LayoutV2',

  components: {
    BiosampleVisGroup,
    EnvironmentVisGroup,
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
    const studySummaryData = useFacetSummaryData({
      field: ref('study_id'),
      table: ref('study'),
      conditions: stateRefs.conditions,
    });
    const study = usePaginatedResults(studySummaryData.otherConditions, api.searchStudy, 3);

    const loggedInUser = computed(() => typeof stateRefs.user.value === 'string');

    const vistab = ref(0);
    const gatedOmicsVisConditions = useClockGate(
      computed(() => (vistab.value === 0)),
      stateRefs.conditions,
    );
    const gatedEnvironmentVisConditions = useClockGate(
      computed(() => (vistab.value === 1)),
      stateRefs.conditions,
    );
    return {
      /* data */
      biosampleType,
      biosample,
      expandedOmicsDetails,
      gatedEnvironmentVisConditions,
      gatedOmicsVisConditions,
      loggedInUser,
      studyType,
      study,
      studyCheckboxState,
      types,
      vistab,
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
            <v-tabs
              v-model="vistab"
              height="30px"
            >
              <v-tab key="omics">
                Omics
              </v-tab>
              <v-tab key="environments">
                Environment
              </v-tab>
            </v-tabs>
            <v-tabs-items
              v-model="vistab"
            >
              <v-tab-item key="omics">
                <BiosampleVisGroup :conditions="gatedOmicsVisConditions" />
              </v-tab-item>
              <v-tab-item key="environments">
                <EnvironmentVisGroup :conditions="gatedEnvironmentVisConditions" />
              </v-tab-item>
            </v-tabs-items>

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
                <template #action-right="{ result }">
                  <v-list-item-action>
                    <v-btn
                      icon
                      plain
                      :to="{ name: 'V2Study', params: { id: result.id } }"
                    >
                      <v-icon color="grey">
                        mdi-information
                      </v-icon>
                    </v-btn>
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
                <template #action-right="{ result }">
                  <v-list-item-action>
                    <v-btn
                      icon
                      plain
                      :to="{ name: 'V2Sample', params: { id: result.id } }"
                    >
                      <v-icon color="grey">
                        mdi-information
                      </v-icon>
                    </v-btn>
                  </v-list-item-action>
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
