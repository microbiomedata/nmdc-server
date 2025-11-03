<script lang="ts">
import {
  defineComponent, reactive, computed, ref, Ref,

} from 'vue';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import { api, Condition, StudySearchResults } from '@/data/api';

import {
  stateRefs, toggleConditions, dataObjectFilter,
} from '@/store';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import usePaginatedResults from '@/use/usePaginatedResults';
import useClockGate from '@/use/useClockGate';
import SampleListExpansion from '@/components/SampleListExpansion.vue';
import AppBanner from '@/components/AppBanner.vue';
import BulkDownload from '@/components/BulkDownload.vue';
import EnvironmentVisGroup from './EnvironmentVisGroup.vue';
import BiosampleVisGroup from './BiosampleVisGroup.vue';
import SearchSidebar from './SearchSidebar.vue';
import SearchHelpMenu from './SearchHelpMenu.vue';

export default defineComponent({
  name: 'SearchLayout',

  components: {
    AppBanner,
    BiosampleVisGroup,
    BulkDownload,
    EnvironmentVisGroup,
    SampleListExpansion,
    SearchResults,
    SearchSidebar,
    SearchHelpMenu,
  },

  setup() {
    const showConsortia = ref(true);
    const showStudies = ref(true);
    /**
     * Study checkbox state logic
     */
    const studyCheckboxState = computed(() => (
      stateRefs.conditions.value
        .filter((c) => c.table === 'study' && c.field === 'study_id')
        .map((c) => c.value)
    ));
    function setChecked(studyId: string, { children = [] as StudySearchResults[], omicsType = '' } = {}) {
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
      if (children.length > 0) {
        children.forEach((child) => {
          if (!studyCheckboxState.value.includes(child.id)) {
            conditions.push({
              value: child.id,
              table: 'study',
              field: 'study_id',
              op: '==',
            });
          }
        });
      }

      toggleConditions(conditions);
    }

    const studyConditions: Ref<Record<string, Condition[]>> = ref<Record<string, Condition[]>>({
      study: [{
        field: 'study_category',
        table: 'study',
        op: '==',
        value: 'research_study',
      }],
      consortia: [{
        field: 'study_category',
        table: 'study',
        op: '==',
        value: 'consortium',
      }],
    });

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
    const studyCondition = computed(() => studyConditions.value.study.concat(studySummaryData.otherConditions.value));
    const consortiumCondition = computed(() => studyConditions.value.consortia.concat(studySummaryData.otherConditions.value));

    const study = usePaginatedResults(ref(studyCondition), api.searchStudy, undefined, 5);
    const consortium = usePaginatedResults(ref(consortiumCondition), api.searchStudy, undefined, 5);

    const studyResults = computed(() => Object.values(study.data.results.results)
      .map((r) => ({
        ...r,
        name: r.annotations.title || r.name,
        children: r.children?.map((c) => ({
          ...c,
          name: c.annotations.title || c.name,
        })),
      })));
    const consortiumStudyResults = computed(() => Object.values(consortium.data.results.results)
      .map((r) => ({
        ...r,
        name: r.annotations.title || r.name,
        children: r.children?.map((c) => ({
          ...c,
          name: c.annotations.title || c.name,
        })),
      })));

    const loggedInUser = computed(() => stateRefs.user.value !== null);

    const vistab = ref(0);
    const gatedOmicsVisConditions = useClockGate(
      computed(() => (vistab.value === 0)),
      stateRefs.conditions,
    );
    const gatedEnvironmentVisConditions = useClockGate(
      computed(() => (vistab.value === 1)),
      stateRefs.conditions,
    );
    const showChildren:Ref<any[]> = ref([]);
    function toggleChildren(value:StudySearchResults) {
      // eslint-disable-next-line no-unused-expressions
      showChildren.value.includes(value.id) ? showChildren.value.splice(showChildren.value.indexOf(value.id), 1) : showChildren.value.push(value.id);
    }

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
      consortium,
      studyResults,
      consortiumStudyResults,
      showConsortia,
      showStudies,
      showChildren,
      studyCheckboxState,
      types,
      vistab,
      toggleChildren,
      /* methods */
      setChecked,
      setExpanded,
      fieldDisplayName,
    };
  },
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
      class="py-0"
    >
      <v-row>
        <v-col>
          <v-row class="align-center">
            <v-col>
              <v-tabs
                v-model="vistab"
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
            v-model="vistab"
            class="my-3"
          >
            <v-window-item key="omics">
              <BiosampleVisGroup
                :conditions="gatedOmicsVisConditions"
                :vistab="vistab"
              />
            </v-window-item>
            <v-window-item key="environments">
              <EnvironmentVisGroup :conditions="gatedEnvironmentVisConditions" />
            </v-window-item>
          </v-window>
          <v-card variant="outlined">
            <v-card
              flat
            >
              <v-card-title
                class="pb-0 d-flex align-center"
              >
                {{ consortium.data.results.count === 1 ? 'Consortium' : 'Consortia' }}
                <v-tooltip
                  right
                >
                  <template #activator="{ props }">
                    <v-btn
                      icon
                      variant="plain"
                      size="small"
                      v-bind="props"
                    >
                      <v-icon>mdi-help-circle</v-icon>
                    </v-btn>
                  </template>
                  <span>Standardized Data Collections</span>
                </v-tooltip>
                <v-spacer />
                <v-card-actions>
                  <v-btn
                    elevation="0"
                    color="primary"
                    variant="elevated"
                    :disabled="consortium.data.results.count === 0"
                    @click="showConsortia=!showConsortia"
                  >
                    {{ showConsortia ? 'Hide' : 'View' }} Consortia
                    <v-icon>
                      {{ showConsortia ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                    </v-icon>
                  </v-btn>
                </v-card-actions>
              </v-card-title>
              <v-expand-transition>
                <div v-show="showConsortia">
                  <SearchResults
                    disable-navigate-on-click
                    :count="consortium.data.results.count"
                    :icon="'mdi-database'"
                    :items-per-page="consortium.data.limit"
                    :results="consortiumStudyResults"
                    :page="consortium.data.pageSync"
                    :loading="consortium.loading.value"
                    @set-page="consortium.setPage($event)"
                    @selected="$router.push({ name: 'Study', params: { id: $event} })"
                    @set-items-per-page="consortium.setItemsPerPage($event)"
                  >
                    <template #action="{ result }">
                      <v-list-item-action>
                        <v-checkbox-btn
                          :input-value="studyCheckboxState"
                          :value="result.id"
                          @click.stop
                          @change="setChecked(result.id,{children:result.children})"
                        />
                      </v-list-item-action>
                    </template>
                    <template #child-list="{ result }">
                      <v-list-item-action
                        v-if="result.children && result.children.length > 0"
                        class="ma-0"
                      >
                        <v-btn
                          icon
                          variant="plain"
                          @click="toggleChildren(result)"
                        >
                          <v-icon
                            v-if="showChildren.includes(result.id)"
                          >
                            mdi-chevron-up-box
                          </v-icon>
                          <v-icon
                            v-else
                          >
                            mdi-chevron-down-box
                          </v-icon>
                        </v-btn>
                      </v-list-item-action>
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
                            mdi-open-in-new
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
                            v-if="item.count"
                            :key="item.type"
                            size="small"
                            class="mr-2 my-1"
                            @click.stop="setChecked(props.result.id, {omicsType:item.type})"
                          >
                            {{ fieldDisplayName(item.type) }}: {{ item.count }}
                          </v-chip>
                        </template>
                      </div>
                      <v-card
                        v-if="showChildren.includes(props.result.id)"
                        flat
                        class="pa-4 mt-2"
                      >
                        <v-divider />
                        <SearchResults
                          disable-navigate-on-click
                          disable-pagination
                          :count="props.result.children.length"
                          :icon="'mdi-database'"
                          :items-per-page="props.result.children.length"
                          :results="props.result.children"
                          :page="1"
                          :loading="false"
                          @selected="$router.push({ name: 'Study', params: { id: $event} })"
                        >
                          <template #action="{ result }">
                            <v-list-item-action>
                              <v-checkbox-btn
                                :disabled="studyCheckboxState.includes(props.result.id)"
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
                                variant="plain"
                                size="large"
                                :to="{ name: 'Study', params: { id: result.id } }"
                              >
                                <v-icon>
                                  mdi-open-in-new
                                </v-icon>
                              </v-btn>
                            </v-list-item-action>
                          </template>
                          <template #item-content="childProps">
                            <div v-if="childProps.result.omics_processing_counts">
                              <template
                                v-for="item in childProps.result.omics_processing_counts"
                              >
                                <v-chip
                                  v-if="item.count"
                                  :key="item.type"
                                  size="small"
                                  class="mr-2 my-1"
                                  @click.stop="setChecked(props.result.id, {omicsType:item.type})"
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
                </div>
              </v-expand-transition>
            </v-card>
            <v-divider />
            <v-card
              flat
            >
              <v-card-title class="pb-0 d-flex align-center">
                {{ study.data.results.count === 1 ? 'Study' : 'Studies' }}
                <v-tooltip
                  right
                >
                  <template #activator="{ props }">
                    <v-btn
                      icon
                      variant="plain"
                      size="small"
                      v-bind="props"
                    >
                      <v-icon>mdi-help-circle</v-icon>
                    </v-btn>
                  </template>
                  <span>Research-driven Experimental Data Sets</span>
                </v-tooltip>
                <v-spacer />
                <v-card-actions>
                  <v-btn
                    elevation="0"
                    color="primary"
                    variant="elevated"
                    :disabled="study.data.results.count === 0"
                    @click="showStudies=!showStudies"
                  >
                    {{ showStudies ? 'Hide' : 'View' }} Studies
                    <v-icon>
                      {{ showStudies ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                    </v-icon>
                  </v-btn>
                </v-card-actions>
              </v-card-title>
              <v-expand-transition>
                <div v-show="showStudies">
                  <SearchResults
                    disable-navigate-on-click
                    :count="study.data.results.count"
                    :icon="studyType.icon"
                    :items-per-page="study.data.limit"
                    :results="studyResults"
                    :page="study.data.pageSync"
                    :loading="study.loading.value"
                    @set-page="study.setPage($event)"
                    @selected="$router.push({ name: 'Study', params: { id: $event} })"
                    @set-items-per-page="study.setItemsPerPage($event)"
                  >
                    <template #action="{ result }">
                      <v-list-item-action>
                        <v-checkbox-btn
                          :input-value="studyCheckboxState"
                          :value="result.id"
                          @click.stop
                          @change="setChecked(result.id, {children:result.children})"
                        />
                      </v-list-item-action>
                    </template>

                    <template #child-list="{ result }">
                      <v-list-item-action
                        v-if="result.children && result.children.length > 0"
                        class="ma-0"
                      >
                        <v-btn
                          icon
                          variant="plain"
                          @click="toggleChildren(result)"
                        >
                          <v-icon
                            v-if="showChildren.includes(result.id)"
                          >
                            mdi-chevron-up-box
                          </v-icon>
                          <v-icon
                            v-else
                          >
                            mdi-chevron-down-box
                          </v-icon>
                        </v-btn>
                      </v-list-item-action>
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
                            mdi-open-in-new
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
                            v-if="item.count"
                            :key="item.type"
                            size="small"
                            class="mr-2 my-1"
                            @click.stop="setChecked(props.result.id, {omicsType:item.type})"
                          >
                            {{ fieldDisplayName(item.type) }}: {{ item.count }}
                          </v-chip>
                        </template>
                      </div>
                      <v-card
                        v-if="showChildren.includes(props.result.id)"
                        flat
                        class="pa-4 mt-2"
                      >
                        <v-divider />
                        <SearchResults
                          disable-navigate-on-click
                          disable-pagination
                          :count="props.result.children.length"
                          :icon="studyType.icon"
                          :items-per-page="props.result.children.length"
                          :results="props.result.children"
                          :page="1"
                          :loading="false"
                          @selected="$router.push({ name: 'Study', params: { id: $event} })"
                        >
                          <template #action="{ result }">
                            <v-list-item-action>
                              <v-checkbox-btn
                                :disabled="studyCheckboxState.includes(props.result.id)"
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
                                variant="plain"
                                size="large"
                                :to="{ name: 'Study', params: { id: result.id } }"
                              >
                                <v-icon>
                                  mdi-open-in-new
                                </v-icon>
                              </v-btn>
                            </v-list-item-action>
                          </template>
                          <template #item-content="childProps">
                            <div v-if="childProps.result.omics_processing_counts">
                              <template
                                v-for="item in childProps.result.omics_processing_counts"
                              >
                                <v-chip
                                  v-if="item.count"
                                  :key="item.type"
                                  size="small"
                                  class="mr-2 my-1"
                                  @click.stop="setChecked(childProps.result.id, {omicsType:item.type})"
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
                </div>
              </v-expand-transition>
            </v-card>
          </v-card>
          <v-card
            variant="outlined"
            class="my-3"
          >
            <div class="ma-3">
              <div class="d-flex align-center">
                <v-card-title class="grow py-0">
                  <span v-if="biosample.loading.value">
                    Samples
                  </span>
                  <span v-else>
                    {{ biosample.data.results.count }}
                    {{ biosample.data.results.count === 1 ? 'Sample' : 'Samples' }}
                  </span>
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
              @set-items-per-page="biosample.setItemsPerPage($event)"
            >
              <template #subtitle="props">
                <span class="pr-2">Study ID:</span>
                <router-link
                  :to="{name: 'Study', params: { id: props.result.study_id }}"
                  class="pr-2 text-grey-darken-4"
                  v-text="props.result.study_id"
                />
                <template
                  v-if="props.result.alternate_identifiers.length || props.result.emsl_biosample_identifiers.length"
                >
                  <span class="pr-2">Sample Identifiers:</span>
                  <a
                    v-for="id in props.result.alternate_identifiers"
                    :key="id"
                    :href="`https://identifiers.org/${id}`"
                    class="pr-2 text-grey-darken-4"
                    target="_blank"
                    rel="noopener noreferrer"
                  >{{ id }}</a>
                  <span
                    v-for="id in props.result.emsl_biosample_identifiers"
                    :key="id"
                  >
                    {{ id }}
                  </span>
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
                    variant="plain"
                    size="large"
                    :to="{ name: 'Sample', params: { id: result.id } }"
                  >
                    <v-icon>
                      mdi-open-in-new
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
</template>
