<script lang="ts">
import {
  defineComponent, reactive, computed, ref,
} from '@vue/composition-api';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
import { fieldDisplayName } from '@/util';
import { api, Condition } from '@/data/api';

import { stateRefs, toggleConditions, dataObjectFilter } from '@/store';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import usePaginatedResults from '@/use/usePaginatedResults';
import useClockGate from '@/use/useClockGate';
import SampleListExpansion from '@/components/SampleListExpansion.vue';

import BulkDownload from '@/components/BulkDownload.vue';
import EnvironmentVisGroup from './EnvironmentVisGroup.vue';
import BiosampleVisGroup from './BiosampleVisGroup.vue';
import SearchSidebar from './SearchSidebar.vue';
import SearchHelpMenu from './SearchHelpMenu.vue';

export default defineComponent({
  name: 'SearchLayout',

  components: {
    BiosampleVisGroup,
    BulkDownload,
    EnvironmentVisGroup,
    SampleListExpansion,
    SearchResults,
    SearchSidebar,
    SearchHelpMenu,
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
    function setChecked(studyId: string, omicsType = '') {
      const conditions: Condition[] = [{
        value: studyId,
        table: 'study',
        op: '==',
        field: 'study_id',
      }];
      if (omicsType) {
        conditions.push({
          value: omicsType,
          table: 'omics_processing',
          field: 'omics_type',
          op: '==',
        });
      }
      toggleConditions(conditions);
    }

    /**
     * SearchLayout-level settings
     */
    const disableBulkDownload = ref(true);
    api.getAppSettings().then((appSettings) => {
      disableBulkDownload.value = appSettings.disable_bulk_download;
    });

    /**
     * Expanded Omics details
     */
    const expandedOmicsDetails = reactive({
      resultId: '',
      omicsProcessingId: '',
    });
    function setExpanded(resultId: string, omicsProcessingId: string) {
      if (expandedOmicsDetails.resultId !== resultId
        || expandedOmicsDetails.omicsProcessingId !== omicsProcessingId) {
        expandedOmicsDetails.resultId = resultId;
        expandedOmicsDetails.omicsProcessingId = omicsProcessingId;
      } else {
        expandedOmicsDetails.resultId = '';
        expandedOmicsDetails.omicsProcessingId = '';
      }
    }

    const biosampleType = types.biosample;
    const biosample = usePaginatedResults(stateRefs.conditions, api.searchBiosample, dataObjectFilter);

    const studyType = types.study;
    const studySummaryData = useFacetSummaryData({
      field: ref('study_id'),
      table: ref('study'),
      conditions: stateRefs.conditions,
    });
    const study = usePaginatedResults(studySummaryData.otherConditions, api.searchStudy, undefined, 50);
    const studyResults = computed(() => Object.values(study.data.results.results));

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
      dataObjectFilter,
      expandedOmicsDetails,
      gatedEnvironmentVisConditions,
      gatedOmicsVisConditions,
      loggedInUser,
      disableBulkDownload,
      studyType,
      study,
      studyResults,
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
    <SearchSidebar :results-count="biosample.data.results.count" />
    <v-main>
      <v-progress-linear
        v-show="biosample.loading.value || study.loading.value"
        indeterminate
        background-opacity="0"
        style="position: fixed; top: 64; z-index: 2;"
      />
      <v-container
        fluid
        class="py-0"
      >
        <v-row>
          <v-col>
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
              </v-col>
              <v-spacer />
              <v-col class="d-flex justify-end flex-grow-0 flex-shrink-0">
                <search-help-menu />
              </v-col>
            </v-row>
            <v-tabs-items
              v-model="vistab"
              class="my-3"
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
                {{ study.data.results.count }}
                {{ study.data.results.count === 1 ? 'Study' : 'Studies' }}
              </v-card-title>
              <SearchResults
                disable-pagination
                :count="study.data.results.count"
                :icon="studyType.icon"
                :items-per-page="study.data.limit"
                :results="studyResults"
                :page="study.data.pageSync"
                :loading="study.loading.value"
                @set-page="study.setPage($event)"
                @selected="$router.push({ name: 'Study', params: { id: $event} })"
              >
                <template #action="{ result }">
                  <v-list-item-action>
                    <v-checkbox
                      :input-value="studyCheckboxState"
                      :value="result.id"
                      @click.stop
                      @change="setChecked(result.id)"
                    />
                  </v-list-item-action>
                </template>
                <template #action-right="{ result }">
                  <v-list-item-action>
                    <v-btn
                      icon
                      large
                      :to="{ name: 'Study', params: { id: result.id } }"
                    >
                      <v-icon>
                        mdi-chevron-right-box
                      </v-icon>
                    </v-btn>
                  </v-list-item-action>
                </template>
                <template #item-content="props">
                  <div v-if="props.result.omics_processing_counts">
                    <template
                      v-for="item in props.result.omics_processing_counts"
                    >
                      <v-chip
                        v-if="item.count && (item.type.toLowerCase() !== 'lipidomics')"
                        :key="item.type"
                        small
                        class="mr-2 my-1"
                        @click.stop="setChecked(props.result.id, item.type)"
                      >
                        {{ fieldDisplayName(item.type) }}: {{ item.count }}
                      </v-chip>
                    </template>
                  </div>
                  <div v-else>
                    <v-chip
                      small
                      disabled
                      class="my-1"
                    >
                      Omics data coming soon
                    </v-chip>
                  </div>
                </template>
              </SearchResults>
            </v-card>
            <v-card
              outlined
              class="my-4"
            >
              <div class="ma-3">
                <div class="d-flex align-center">
                  <v-card-title class="grow py-0">
                    {{ biosample.data.results.count }}
                    {{ biosample.data.results.count === 1 ? 'Sample' : 'Samples' }}
                  </v-card-title>
                  <v-spacer />
                  <div
                    v-if="!disableBulkDownload"
                    style="width: 70%"
                  >
                    <BulkDownload
                      :disabled="!loggedInUser"
                      :search-result-count="biosample.data.results.count"
                    />
                  </div>
                </div>
              </div>
              <SearchResults
                disable-navigate-on-click
                :count="biosample.data.results.count"
                :icon="biosampleType.icon"
                :items-per-page="biosample.data.limit"
                :results="biosample.data.results.results"
                :page="biosample.data.pageSync"
                :subtitle-key="'study_id'"
                :loading="biosample.loading.value"
                @set-page="biosample.setPage($event)"
                @selected="$router.push({ name: 'Sample', params: { id: $event }})"
              >
                <template #subtitle="props">
                  <span class="pr-2">Study ID:</span>
                  <router-link
                    :to="{name: 'Study', params: { id: props.result.study_id }}"
                    class="pr-2 grey--text text--darken-2"
                    v-text="props.result.study_id"
                  />
                  <template
                    v-if="(props.result.alternative_identifiers && props.result.alternative_identifiers.length) ||
                      (props.result.emsl_biosample_identifiers && props.result.emsl_biosample_identifiers.length)"
                  >
                    <span class="pr-2">Sample Identifiers:</span>
                    <template v-if="props.result.alternative_identifiers">
                      <a
                        v-for="id in props.result.alternative_identifiers"
                        :key="id"
                        :href="`https://identifiers.org/${id}`"
                        class="pr-2 grey--text text--darken-2"
                        target="_blank"
                        rel="noopener noreferrer"
                      >{{ id }}</a>
                    </template>
                    <template v-if="props.result.emsl_biosample_identifiers">
                      <span
                        v-for="id in props.result.emsl_biosample_identifiers"
                        :key="id"
                      >
                        {{ id }}
                      </span>
                    </template>
                  </template>
                </template>
                <template #item-content="props">
                  <SampleListExpansion
                    v-bind="{
                      result: props.result,
                      expanded: expandedOmicsDetails,
                      loggedInUser,
                      showBulk: dataObjectFilter.length > 0,
                    }"
                    @open-details="setExpanded(props.result.id, $event)"
                  />
                </template>
                <template #action-right="{ result }">
                  <v-list-item-action>
                    <v-btn
                      icon
                      large
                      :to="{ name: 'Sample', params: { id: result.id } }"
                    >
                      <v-icon>
                        mdi-chevron-right-box
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
