<script setup lang="ts">
import {
  computed, ref,

} from 'vue';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import { api, Condition, StudySearchResults } from '@/data/api';

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
import EnvironmentVisGroup from './EnvironmentVisGroup.vue';
import BiosampleVisGroup from './BiosampleVisGroup.vue';
import SearchSidebar from './SearchSidebar.vue';
import SearchHelpMenu from './SearchHelpMenu.vue';
import BiosampleSearchResults from '@/components/Presentation/BiosampleSearchResults.vue';

/**
 * Study checkbox state logic
 */
const studyCheckboxState = computed(() => (
  stateRefs.conditions.value
    .filter((c) => c.table === 'study' && c.field === 'study_id')
    .map((c) => c.value as string)
));

/**
 * Set a study (or consortium) as checked in the search results.
 * @param checked - Whether the item is currently being checked (true) or unchecked (false)
 * @param studyId - ID of the study to select
 * @param children - Optional children studies to also select
 */
function setChecked(checked: boolean, studyId: string, children: StudySearchResults[] = []) {
  const conditions: Condition[] = [{
    value: studyId,
    table: 'study',
    op: '==',
    field: 'study_id',
  }];
  if (children.length > 0) {
    children.forEach((child) => {
      conditions.push({
        value: child.id,
        table: 'study',
        field: 'study_id',
        op: '==',
      });
    });
  }
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
const studyCondition = studySummaryData.otherConditions.value || [];
const study = usePaginatedResults(ref(studyCondition), api.searchStudy, undefined, 10);
const studyResults = computed<StudySearchResults[]>(() => Object.values(study.data.results.results)
  .map((r) => ({
    ...r,
    name: r.annotations.title || r.name,
    children: r.children?.map((c) => ({
      ...c,
      name: c.annotations.title || c.name,
    })),
  })));

const loggedInUser = computed(() => stateRefs.user.value !== null);

const visTab = ref(0);
const resultsTab = ref(0);
const gatedOmicsVisConditions = useClockGate(
  computed(() => (visTab.value === 0)),
  stateRefs.conditions,
);
const gatedEnvironmentVisConditions = useClockGate(
  computed(() => (visTab.value === 1)),
  stateRefs.conditions,
);
// const showChildren:Ref<any[]> = ref([]);
// function toggleChildren(value:StudySearchResults) {
//   showChildren.value.includes(value.id) ? showChildren.value.splice(showChildren.value.indexOf(value.id), 1) : showChildren.value.push(value.id);
// }
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
      class="py-0"
    >
      <v-row>
        <v-col>
          <v-row class="align-center">
            <v-col>
              <v-tabs
                v-model="visTab"
                color="primary"
              >
                <v-tab key="omics">
                  Data Type
                </v-tab>
                <v-tab key="environments">
                  Environment
                </v-tab>
              </v-tabs>
            </v-col>
            <v-col class="d-flex justify-end flex-grow-0 flex-shrink-0">
              <search-help-menu />
            </v-col>
          </v-row>
          <v-window
            v-model="visTab"
            class="my-3"
          >
            <v-window-item key="omics">
              <BiosampleVisGroup
                :conditions="gatedOmicsVisConditions"
                :vis-tab="visTab"
              />
            </v-window-item>
            <v-window-item key="environments">
              <EnvironmentVisGroup :conditions="gatedEnvironmentVisConditions" />
            </v-window-item>
          </v-window>
          <v-card variant="outlined">
            <v-tabs
              v-model="resultsTab"
              color="primary"
            >
              <v-tab key="studies">
                Studies ({{ study.data.results.count }})
              </v-tab>
              <v-tab key="samples">
                Samples ({{ biosample.data.results.count }})
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
              v-model="resultsTab"
            >
              <v-tabs-window-item key="studies">
                <SearchResults
                  show-checkbox
                  :count="study.data.results.count"
                  :icon="studyType.icon"
                  :items-per-page="study.data.limit"
                  :results="studyResults"
                  :page="study.data.pageSync"
                  :checkbox-values="studyCheckboxState"
                  @set-page="study.setPage($event)"
                  @selected="$router.push({ name: 'Study', params: { id: $event} })"
                  @set-items-per-page="study.setItemsPerPage($event)"
                  @checkbox-change="setChecked($event.checked, $event.id, $event.children as StudySearchResults[])"
                >
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
                    <div v-if="result.omics_processing_counts">
                      <template
                        v-for="item in result.omics_processing_counts"
                      >
                        <v-chip
                          v-if="(item as any).count"
                          :key="(item as any).type"
                          size="small"
                          class="mr-2 my-1"
                          @click.stop="selectStudyAndOmics(result.id, (item as any).type)"
                        >
                          {{ fieldDisplayName((item as any).type) }}: {{ (item as any).count }}
                        </v-chip>
                      </template>
                    </div>
                  </template>
                  <template #item-children="{ result }">
                    <v-card
                      v-if="result.children?.length"
                      flat
                      class="pa-4 mt-2"
                    >
                      <v-divider />
                      <SearchResults
                        show-checkbox
                        disable-pagination
                        :count="result.children.length"
                        :icon="studyType.icon"
                        :items-per-page="result.children.length"
                        :results="result.children"
                        :page="1"
                        :checkbox-values="studyCheckboxState"
                        :checkbox-disabled="studyCheckboxState.includes(result.id)"
                        @selected="$router.push({ name: 'Study', params: { id: $event} })"
                        @checkbox-change="setChecked($event.checked, $event.id)"
                      >
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
              <v-tabs-window-item key="samples">
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
