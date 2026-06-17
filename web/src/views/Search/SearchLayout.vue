<script setup lang="ts">
import {
  computed, Ref, ref,
  watch,

} from 'vue';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import { api, Condition, StudySearchResult } from '@/data/api';

import {
  stateRefs, dataObjectFilter,
  setConditions,
  removeConditions,
} from '@/store';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import usePaginatedResults from '@/use/usePaginatedResults';
import useClockGate from '@/use/useClockGate';
import AppBanner from '@/components/AppBanner.vue';
import BulkDownload from '@/components/BulkDownload.vue';
import ClickToCopyText from '@/components/Presentation/ClickToCopyText.vue';
import EnvironmentVisGroup from './EnvironmentVisGroup.vue';
import BiosampleVisGroup from './BiosampleVisGroup.vue';
import AnalysisVizGroup from './AnalysisVizGroup.vue';
import SearchSidebar from './SearchSidebar.vue';
import SearchHelpMenu from './SearchHelpMenu.vue';
import BiosampleSearchResults from '@/components/Presentation/BiosampleSearchResults.vue';
import { useRoute, useRouter } from 'vue-router';

const biosampleDescription = NmdcSchema.classes[types.biosample.schemaName].description;
// TODO: would we rather use the study description from the schema?
// const studyDescription = NmdcSchema.classes[types.study.schemaName].description;
const studyDescription = 'Research-driven experimental datasets and standardized data collections.';

const route = useRoute();
const router = useRouter();

/**
 * Study checkbox state logic
 */
const studyCheckboxState = computed(() => (
  stateRefs.conditions.value
    .filter((c) => c.table === 'study' && c.field === 'study_id')
    .map((c) => c.value as string)
));

/**
 * Set a study as checked in the search results.
 * @param checked - Whether the item is currently being checked (true) or unchecked (false)
 * @param studyId - ID of the study to select
 */
function setChecked(checked: boolean, studyId: string) {
  const conditions: Condition[] = [{
    value: studyId,
    table: 'study',
    op: '==',
    field: 'study_id',
  }];
  if (checked) {
    setConditions([...stateRefs.conditions.value, ...conditions]);
  } else {
    removeConditions(conditions);
  }
}

/**
 * Set study and omics type conditions.
 * Used when clicking on omics processing count chips.
 * @param studyId - ID of the study to select
 * @param omicsType - Type of omics processing to select 
 */
function selectStudyAndOmics(studyId: string, omicsType: string) {
  const conditions: Condition[] = [{
    value: studyId,
    table: 'study',
    op: '==',
    field: 'study_id',
  },
  {
    value: omicsType,
    table: 'omics_processing',
    field: 'omics_type',
    op: '==',
  }];
  setConditions([...stateRefs.conditions.value, ...conditions]);
}

/**
 * SearchLayout-level settings
 */
const disableBulkDownload = ref(true);
api.getAppSettings().then((appSettings) => {
  disableBulkDownload.value = appSettings.disable_bulk_download;
});

const biosample = usePaginatedResults(stateRefs.conditions, api.searchBiosample, dataObjectFilter, 10);
const studyType = types.study;
const studySummaryData = useFacetSummaryData({
  field: ref('study_id'),
  table: ref('study'),
  conditions: stateRefs.conditions,
});
const study = usePaginatedResults(studySummaryData.otherConditions, api.searchStudy, undefined, 10);
const studyResults = computed<StudySearchResult[]>(() => Object.values(study.data.results.results)
  .map((r) => ({
    ...r,
    name: r.annotations.title || r.name,
    children: r.children?.map((c) => ({
      ...c,
      name: c.annotations.title || c.name,
    })),
  })));

const loggedInUser = computed(() => stateRefs.user.value !== null);

const visTabs = ref(['data', 'analysis', 'environment']);
const resultsTabs = ref(['studies', 'samples']);
const activeVisTab = ref(route.query.view as string || visTabs.value[0]);
const activeResultsTab = ref(route.query.results as string || resultsTabs.value[0]);
const gatedOmicsVisConditions = useClockGate(
  computed(() => (activeVisTab.value === visTabs.value[0])),
  stateRefs.conditions,
);
const gatedEnvironmentVisConditions = useClockGate(
  computed(() => (activeVisTab.value === visTabs.value[2])),
  stateRefs.conditions,
);
const showChildren: Ref<any[]> = ref([]);
function toggleChildren(value:StudySearchResult) {
  showChildren.value.includes(value.id) ? showChildren.value.splice(showChildren.value.indexOf(value.id), 1) : showChildren.value.push(value.id);
}

watch([activeVisTab, activeResultsTab], ([newVisTab, newResultsTab]) => {
  const { view, results, ...rest } = route.query;
  router.replace({ query: { view: newVisTab, results: newResultsTab, ...rest } })
});
</script>

<template>
  <SearchSidebar
    :results-count="biosample.data.results.count"
    :is-loading="biosample.loading.value"
  />
  <v-main>
    <v-progress-linear
      v-show="biosample.loading.value || study.loading.value"
      indeterminate
      background-opacity="0"
      style="position: fixed; top: 64; z-index: 2;"
    />
    <AppBanner />
    <v-container
      fluid
      class="py-3"
    >
      <v-row>
        <v-col>
          <div class="d-flex align-center mb-3">
            <div class="font-weight-bold text-title-2 text-primary flex-grow-1">
              <span v-if="biosample.loading.value">
                Loading results...
              </span>
              <span
                v-else
                class="d-flex align-center"
              >
                <span>Found {{ biosample.data.results.count }} samples</span>
              </span>
            </div>
            <SearchHelpMenu />
          </div>
          <v-card
            class="mb-3" 
            variant="outlined"
          >
            <v-tabs
              v-model="activeVisTab"
              color="primary"
            >
              <v-tab :value="visTabs[0]">
                <v-icon class="mr-1">
                  mdi-map-marker-outline
                </v-icon>
                Data
              </v-tab>
              <v-tab :value="visTabs[1]">
                <v-icon class="mr-1">
                  mdi-chart-box-outline
                </v-icon>
                Analysis
              </v-tab>
              <v-tab :value="visTabs[2]">
                <v-icon class="mr-1">
                  mdi-chart-sankey-variant
                </v-icon>
                Environment
              </v-tab>
            </v-tabs>
            <v-divider />
            <v-window
              v-model="activeVisTab"
            >
              <v-window-item :value="visTabs[0]">
                <BiosampleVisGroup
                  :conditions="gatedOmicsVisConditions"
                  :vis-tab="activeVisTab"
                />
              </v-window-item>
              <v-window-item :value="visTabs[1]">
                <AnalysisVizGroup
                  :conditions="gatedOmicsVisConditions"
                  :vis-tab="activeVisTab"
                />
              </v-window-item>
              <v-window-item :value="visTabs[2]">
                <EnvironmentVisGroup :conditions="gatedEnvironmentVisConditions" />
              </v-window-item>
            </v-window>
          </v-card>
          <v-card variant="outlined">
            <v-tabs
              v-model="activeResultsTab"
              color="primary"
            >
              <v-tab :value="resultsTabs[0]">
                <div class="d-flex align-center ga-2">
                  <span>Studies ({{ study.data.results.count }})</span>
                  <v-tooltip location="top">
                    <template #activator="{ props }">
                      <v-icon
                        v-bind="props"
                        color="grey-darken-1"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>{{ studyDescription }}</span>
                  </v-tooltip>
                </div>
              </v-tab>
              <v-tab :value="resultsTabs[1]">
                <div class="d-flex align-center ga-2">
                  <span>Samples ({{ biosample.data.results.count }})</span>
                  <v-tooltip location="top">
                    <template #activator="{ props }">
                      <v-icon
                        v-bind="props"
                        color="grey-darken-1"
                      >
                        mdi-help-circle
                      </v-icon>
                    </template>
                    <span>{{ biosampleDescription }}</span>
                  </v-tooltip>
                </div>
              </v-tab>
              <v-spacer />
              <div 
                v-if="!disableBulkDownload"
                class="d-flex align-center mr-4"
              >
                <BulkDownload
                  :disabled="!loggedInUser"
                  :search-result-count="biosample.data.results.count"
                />
              </div>
            </v-tabs>
            <v-divider />
            <v-tabs-window
              v-model="activeResultsTab"
            >
              <v-tabs-window-item :value="resultsTabs[0]">
                <SearchResults
                  :count="study.data.results.count"
                  :icon="studyType.icon"
                  :items-per-page="study.data.limit"
                  :results="studyResults"
                  :page="study.data.pageSync"
                  @set-page="study.setPage($event)"
                  @set-items-per-page="study.setItemsPerPage($event)"
                >
                  <template #action-left="{ result }">
                    <v-list-item-action>
                      <v-checkbox-btn
                        :model-value="studyCheckboxState"
                        :value="result.id"
                        @click.stop
                        @change="setChecked($event.target.checked, result.id)"
                      />
                    </v-list-item-action>
                  </template>
                  <template #item-title="{ result }">
                    <div class="d-flex align-center">
                      <router-link
                        :to="{ name: 'Study', params: { id: result.id }}"
                      >
                        <span class="text-subtitle-2">
                          {{ result.name }}
                        </span>
                      </router-link>
                      <v-list-item-action
                        v-if="result.children && result.children.length > 0"
                        class="ml-2"
                      >
                        <v-btn
                          variant="flat"
                          color="grey-darken-1"
                          size="x-small"
                          @click="toggleChildren(result as StudySearchResult)"
                        >
                          {{ result.children.length }} child {{ result.children.length > 1 ? 'studies' : 'study' }}
                          <template #append>
                            <v-icon>
                              {{ showChildren.includes(result.id) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                            </v-icon>
                          </template>
                        </v-btn>
                      </v-list-item-action>
                    </div>
                  </template>
                  <template #item-subtitle="{ result }">
                    <div class="d-flex ga-1">
                      <span class="flex-shrink-0 text-no-wrap">
                        <strong class="mr-1">ID:</strong>
                        <ClickToCopyText>
                          {{ result.id }}
                        </ClickToCopyText>
                      </span>
                      <v-icon>mdi-circle-small</v-icon>
                      <span class="text-truncate flex-grow-1">{{ result.description }}</span>
                    </div>
                  </template>
                  <template #action-right="{ result }">
                    <v-list-item-action>
                      <v-btn
                        icon
                        variant="plain"
                        size="large"
                        :to="{ name: 'Study', params: { id: result.id } }"
                      >
                        <v-icon>
                          mdi-chevron-right
                        </v-icon>
                      </v-btn>
                    </v-list-item-action>
                  </template>
                  <template #item-content="{ result }">
                    <div 
                      v-if="result.omics_processing_counts"
                      class="d-flex ga-2"
                    >
                      <template
                        v-for="item in result.omics_processing_counts"
                      >
                        <v-chip
                          v-if="item.count"
                          :key="item.type"
                          size="small"
                          @click.stop="selectStudyAndOmics(result.id, item.type)"
                        >
                          {{ fieldDisplayName(item.type) }}: {{ item.count }}
                        </v-chip>
                      </template>
                    </div>
                  </template>
                  <template #item-children="{ result }">
                    <v-card
                      v-if="showChildren.includes(result.id) && result.children?.length"
                      flat
                      class="ml-6 mr-6"
                    >
                      <SearchResults
                        disable-pagination
                        :count="result.children.length"
                        :icon="studyType.icon"
                        :items-per-page="result.children.length"
                        :results="result.children"
                        :page="1"
                      >
                        <template #action-left="{ result: child }">
                          <v-list-item-action>
                            <v-icon color="grey-darken-1">
                              mdi-arrow-right-bottom
                            </v-icon>
                            <span
                              v-tooltip="{
                                text: 'This study is already selected because its parent is selected.',
                                disabled: !studyCheckboxState.includes(result.id),
                                location: 'bottom',
                              }"
                              location="bottom"
                              class="d-inline-block"
                            >
                              <v-checkbox-btn
                                :model-value="studyCheckboxState"
                                :value="child.id"
                                :disabled="studyCheckboxState.includes(result.id)"
                                @click.stop
                                @change="setChecked($event.target.checked, child.id)"
                              />
                            </span>
                          </v-list-item-action>
                        </template>
                        <template #item-title="{ result: child }">
                          <router-link
                            :to="{ name: 'Study', params: { id: child.id }}"
                          >
                            <span class="text-subtitle-2">
                              {{ child.name }}
                            </span>
                          </router-link>
                        </template>
                        <template #item-subtitle="{ result: child }">
                          <div class="d-flex ga-1">
                            <span class="flex-shrink-0 text-no-wrap">
                              <strong class="mr-1">ID:</strong>
                              <ClickToCopyText>
                                {{ child.id }}
                              </ClickToCopyText>
                            </span>
                            <v-icon>mdi-circle-small</v-icon>
                            <span class="text-truncate flex-grow-1">{{ child.description }}</span>
                          </div>
                        </template>
                        <template #action-right="{ result: child }">
                          <v-list-item-action>
                            <v-btn
                              icon
                              variant="plain"
                              size="large"
                              :to="{ name: 'Study', params: { id: child.id } }"
                            >
                              <v-icon>
                                mdi-chevron-right
                              </v-icon>
                            </v-btn>
                          </v-list-item-action>
                        </template>
                        <template #item-content="{ result: child }">
                          <div v-if="child.omics_processing_counts">
                            <template
                              v-for="item in child.omics_processing_counts"
                            >
                              <v-chip
                                v-if="item.count"
                                :key="item.type"
                                size="small"
                                class="mr-2 my-1"
                                @click.stop="selectStudyAndOmics(child.id, item.type)"
                              >
                                {{ fieldDisplayName(item.type) }}: {{ item.count }}
                              </v-chip>
                            </template>
                          </div>
                        </template>
                      </SearchResults>
                    </v-card>
                  </template>
                </SearchResults>
              </v-tabs-window-item>
              <v-tabs-window-item :value="resultsTabs[1]">
                <BiosampleSearchResults
                  :data-object-filter="dataObjectFilter"
                  :biosample-search="biosample"
                />
                <h2 v-if="biosample.data.results.count === 0">
                  No results for selected conditions in sample table
                </h2>
              </v-tabs-window-item>
            </v-tabs-window>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-main>
</template>
