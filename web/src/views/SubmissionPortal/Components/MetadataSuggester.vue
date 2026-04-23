<script setup lang="ts">
/**
 * Component to display metadata suggestions and allow users to accept or reject them.
 */
import { computed, ref, watchEffect } from 'vue';
import {
  fetchSuggestionsFromSampleRows,
  removeMetadataSuggestions,
  metadataSuggestions,
  suggestionMode,
  suggestionType,
  fetchSuggestionsFromSampleRowsRequest,
  fetchSuggestionsFromStudyInfoRequest,
} from '@/views/SubmissionPortal/store';
import {
  CellData,
  MetadataSuggestion,
  SuggestionsMode,
  SuggestionFill,
  SuggestionType,
} from '@/views/SubmissionPortal/types';
import type HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi';
import { getRejectedSuggestions, setRejectedSuggestions } from '@/store/localStorage';
import { AI_SUGGESTION_BG } from '@/views/SubmissionPortal/colors.ts';

interface MetadataSuggesterProps {
  /**
   * The submission ID.
   */
  submissionId: string;
  /**
   * Whether the suggester UI is displayed or not. If false, the component will display a message indicating that
   * the user does not have permission to edit the metadata.
   */
  enabled: boolean;
  /**
   * The Harmonizer API instance.
   */
  harmonizerApi: HarmonizerApi;
  /**
   * The schema class name for the active template.
   */
  schemaClassName: string;
}

const aiMenuOpen = ref(false);
const selectedAiOption = ref<string | null>(null);

const aiSuggestionOptions = [
  { label: 'By Row', value: 'by_row' },
  { label: 'By Column', value: 'by_column' },
  { label: 'By Sample Type', value: 'by_sample_type' },
];

const mockSuggestions: Record<string, MetadataSuggestion[]> = {
  'by_row': [
    {
      type: 'replace',
      row: 0,
      slot: 'elev',
      value: '278.3',
      current_value: '325',
      source: 'Suggested based on other metadata in the same row',
      is_ai_generated: true,
    },
    {
      type: 'add',
      row: 1,
      slot: 'depth',
      value: '0.15',
      current_value: null,
      source: 'Suggested based on other metadata in the same row',
      is_ai_generated: true,
    },
  ],
  'by_column': [
    {
      type: 'attention',
      row: null,
      slot: 'ecosystem',
      value: 'Environmental',
      current_value: 'null',
      source: 'Suggested based on values entered in the same column',
      is_ai_generated: true,
    },
    {
      type: 'add',
      row: null,
      slot: 'env_broad_scale',
      value: '__temperate woodland biome [ENVO:01000221]',
      current_value: null,
      source: 'Based on the study context, samples were collected from woodland biomes',
      is_ai_generated: true,
    },
  ],
  // 'by_sample_type': [
  //   {
  //     type: 'replace',
  //     row: 0,
  //     slot: 'samp_name',
  //     value: 'Soil_ex_1',
  //     current_value: 'sample_1',
  //     source: 'Sample name follows convention for soil core samples based on study methodology',
  //     is_ai_generated: true,
  //   },
  //   {
  //     type: 'add',
  //     row: 1,
  //     slot: 'metagenomics; natural organic matter',
  //     value: 'core',
  //     current_value: null,
  //     source: 'Sample type inferred from study description and selected sample environment',
  //     is_ai_generated: true,
  //   },
  // ],
};

interface SuggestionGroup {
  label: string;
  suggestions: MetadataSuggestion[];
}

const mockGroupSuggestions: SuggestionGroup[] = [
  {
    label: 'Soil Samples',
    suggestions: [
      {
        type: 'add',
        row: 0, 
        slot: 'env_broad_scale',
        value: '__temperate woodland biome [ENVO:01000221]',
        current_value: null,
        is_ai_generated: true,
        source: 'Based on the study context, samples were collected from woodland biomes',
      },
      {
        type: 'replace',
        row: 1,
        slot: 'elev',
        value: '278.3',
        current_value: '325',
        is_ai_generated: false,
        source: 'Suggested based on other metadata in the same row',
      },
    ],
  },
  {
    label: 'Water Samples',
    suggestions: [
      {
        type: 'add',
        row: 6,
        slot: 'env_broad_scale',
        value: '__oceanic epipelagic zone biome [ENVO:01000035]',
        current_value: 'null',
        is_ai_generated: true,
        source: 'Suggested based on values entered in the same column',
      },
      {
        type: 'add',
        row: 7,
        slot: 'depth',
        value: '2.5',
        current_value: null,
        is_ai_generated: true,
        source: 'Typical depth for water samples based on this study',
      },
    ],
  },
];

const dismissedGroups = ref<string[]>([]);

const visibleGroups = computed(() => (
  mockGroupSuggestions.filter((group) => !dismissedGroups.value.includes(group.label))
));

function handleDismissGroup(label: string) {
  dismissedGroups.value.push(label);
}

function handleAcceptGroup(group: SuggestionGroup) {
  acceptSuggestions(group.suggestions.filter(canAcceptSuggestion));
  dismissedGroups.value.push(group.label);
}

const aiButtonLabel = computed(() => {
  if (selectedAiOption.value === null) return "Start AI Suggestion";
  return aiSuggestionOptions.find((option) => option.value === selectedAiOption.value)?.label ?? "Start AI Suggestion";
});

// const suggestionModeOptions = Object.values(SuggestionsMode);
// const suggestionFillOptions = Object.values(SuggestionFill);
// const suggestionTypeOptions = Object.values(SuggestionType);

function getSuggestionKey(suggestion: MetadataSuggestion) {
  return `${suggestion.row}__${suggestion.slot}__${suggestion.value}`;
}

const props = defineProps<MetadataSuggesterProps>();

const rejectedSuggestions = ref([] as string[]);
const onDemandSuggestionsLoading = ref(false);

// When the route or schema class name changes (because of changing the active template tab), update the rejected
// suggestions list from local storage.
watchEffect(() => {
  rejectedSuggestions.value = getRejectedSuggestions(props.submissionId, props.schemaClassName);
});

// Suggestions that have been neither accepted nor rejected.
const pendingSuggestions = computed(() => (
    metadataSuggestions.value
      .filter((suggestion) => {
        const key = getSuggestionKey(suggestion);
        return !rejectedSuggestions.value.includes(key);
      })
      .sort((a, b) => {
        // Put suggestions with a specific row number before those without, and sort by row number ascending
        if (a.row !== null && b.row === null) {
          return -1;
        }
        if (a.row === null && b.row !== null) {
          return 1;
        }
        if (a.row !== null && b.row !== null) {
          return a.row - b.row;
        }
        // If both suggestions have no row number, sort by slot name
        return a.slot.localeCompare(b.slot);
      })
));

const hasSuggestions = computed(() => pendingSuggestions.value.length > 0);

/**
 * Accepts the given suggestions by setting the cell data via the Harmonizer API and removing the suggestions from
 * the store.
 * @param suggestions
 */
function acceptSuggestions(suggestions: MetadataSuggestion[]) {
  const cellData = [] as CellData[];
  suggestions.forEach((suggestion) => {
    const { row, slot, value} = suggestion;
    const col = props.harmonizerApi.slotInfo.get(slot)?.columnIndex;
    if (col === undefined || row === null || value === null) {
      return;
    }
    cellData.push({ row, col, text: value });
  });

  // Do this outside of the forEach so that the DataHarmonizer afterChange hook is only triggered once
  props.harmonizerApi.setCellData(cellData);

  removeMetadataSuggestions(props.submissionId, props.schemaClassName, suggestions);
}

/**
 * Rejects the given suggestions by adding them to the rejected suggestions list in local storage.
 * @param suggestions
 */
function rejectSuggestions(suggestions: MetadataSuggestion[]) {
  suggestions.forEach((suggestion) => {
    const key = getSuggestionKey(suggestion);
    rejectedSuggestions.value.push(key);
  });
  setRejectedSuggestions(props.submissionId, props.schemaClassName, rejectedSuggestions.value);
}

/**
 * Handles jumping to the cell associated with the given suggestion.
 * @param suggestion
 */
function handleJumpToCell(suggestion: MetadataSuggestion) {
  const { row, slot } = suggestion;
  const col = props.harmonizerApi.slotInfo.get(slot)?.columnIndex;
  if (col === undefined) {
    return;
  }
  props.harmonizerApi.jumpToRowCol(row || 0, col);
}

function handleSuggestionHover(suggestion: MetadataSuggestion) {
  const { row, slot } = suggestion;
  const col = props.harmonizerApi.slotInfo.get(slot)?.columnIndex;
  if (col === undefined || row === null) {
    return;
  }
  props.harmonizerApi.highlight(row || 0, col);
}

function handleSuggestionLeave() {
  props.harmonizerApi.highlight();
}

/**
 * Handle clicking the reject button for a single suggestion.
 * @param suggestion
 */
function handleRejectSuggestion(suggestion: MetadataSuggestion) {
  rejectSuggestions([suggestion]);
}

/**
 * Handle clicking the accept button for a single suggestion.
 * @param suggestion
 */
function handleAcceptSuggestion(suggestion: MetadataSuggestion) {
  acceptSuggestions([suggestion]);
}

/**
 * Determine if a suggestion can be accepted. A suggestion can be accepted if it has a non-null value and row number.
 * @param suggestion
 */
function canAcceptSuggestion(suggestion: MetadataSuggestion) {
  return suggestion.value !== null && suggestion.row !== null;
}

/**
 * Handle clicking the accept all button.
 */
function handleAcceptAllSuggestions() {
  acceptSuggestions(pendingSuggestions.value.filter(canAcceptSuggestion));
}

/**
 * Handle clicking the reject all button.
 */
function handleRejectAllSuggestions() {
  rejectSuggestions(pendingSuggestions.value);
}

/**
 * Handle clicking the "Suggest for Selected Rows" button.
 *
 * This will get the data for the selected rows, send it to the backend to get suggestions, and then add the
 * suggestions to the store.
 */
function handleAiSuggestionOption(option: string) {
  selectedAiOption.value = option;
  if (option === 'by_sample_type') {
    metadataSuggestions.value = [];
    dismissedGroups.value = [];
  } else {
    metadataSuggestions.value = mockSuggestions[option] ?? [];
  }
  // metadataSuggestions.value = mockSuggestions[option] ?? [];
  // await handleSuggestForSelectedRows();
}

async function handleSuggestForSelectedRows() {
  onDemandSuggestionsLoading.value = true;
  const selectedRanges = props.harmonizerApi.getSelectedCells();
  // selectedRanges is an array of arrays, representing all (possibly discontinuous) ranges of selected cells. Each
  // inner array is [startRow, startCol, endRow, endCol]. Reduce this to a flat array of row numbers contained in
  // the selected ranges.
  const rows = selectedRanges.reduce((acc, range) => {
    if (range[0] === undefined || range[2] === undefined) {
      return acc;
    }
    for (let i = range[0]; i <= range[2]; i += 1) {
      acc.push(i);
    }
    return acc;
  }, [] as number[]);
  const changedRowData = props.harmonizerApi.getDataByRows(rows);
  try {
    await fetchSuggestionsFromSampleRows(props.submissionId, props.schemaClassName, changedRowData);
  } finally {
    onDemandSuggestionsLoading.value = false;
  }
}

/**
 * Handle resetting the rejected suggestions list.
 */
function handleResetRejectedSuggestions() {
  rejectedSuggestions.value = [];
  setRejectedSuggestions(props.submissionId, props.schemaClassName, rejectedSuggestions.value);
}

/**
 * Translate a slot name to its title.
 * @param slot
 */
function getSlotTitle(slot: string) {
  return props.harmonizerApi.slotInfo.get(slot)?.title ?? slot;
}

const loading = computed(() => (
  fetchSuggestionsFromSampleRowsRequest.loading.value || fetchSuggestionsFromStudyInfoRequest.loading.value
));
</script>

<template>
  <v-card
    elevation="0"
    tile
    :loading="loading"
  >
    <template #loader="{ isActive }">
      <v-progress-linear
        :active="isActive"
        color="primary"
        height="2"
        indeterminate
      />
    </template>
    <v-defaults-provider
      :defaults="{
        VSelect: {
          density: 'compact',
          variant: 'outlined',
        },
        VTooltip: {
          location: 'bottom',
          maxWidth: '500px',
          openDelay: 600,
        }
      }"
    >
      <v-card-title class="d-flex align-center mb-3">
        <span>Metadata Suggester</span>
        <v-spacer />
        <v-tooltip bottom>
          <span>
            As you enter sample metadata, the Metadata Suggester will offer suggestions for metadata values based on the
            metadata values you have already entered.
          </span>
          <template #activator="{ props: activatorProps }">
            <v-icon
              size="x-small"
              v-bind="activatorProps"
            >
              mdi-information-outline
            </v-icon>
          </template>
        </v-tooltip>
      </v-card-title>

      <v-card-text v-if="enabled">
        <v-row dense>
          <v-col>
            <v-menu
              v-model="aiMenuOpen"
              :close-on-content-click="true"
            >
              <template #activator="{ props: menuProps }">
                <v-btn
                  color="primary"
                  block
                  v-bind="menuProps"
                >
                  {{ aiButtonLabel }}
                  <v-icon end>
                    mdi-chevron-down
                  </v-icon>
                </v-btn>
                <div 
                  v-if="selectedAiOption !== null"
                  class="text-caption text-medium-emphasis text-center mt-1"
                >
                  Click to change mode
                </div>
              </template>
              <v-list>
                <v-list-item
                  v-for="option in aiSuggestionOptions"
                  :key="option.value"
                  :title="option.label"
                  @click="handleAiSuggestionOption(option.value)"
                />
              </v-list>
            </v-menu>
          </v-col>
        </v-row>


        <!-- <v-row>
          <v-col>
            <v-btn
              color="primary"
              block
              @click="aiSuggestionStarted = true"
            >
              Start AI Suggestion
            </v-btn>
          </v-col>
        </v-row>

        <v-row v-if="suggestionMode === SuggestionFill.BY_ROW && aiSuggestionStarted">
          <v-col cols="12">
            <v-select
              v-model="suggestionFill"
              :items="suggestionFillOptions"
              hide-details
              label="Suggestion Fill"
            />
          </v-col>
        </v-row> -->

        <!-- <v-row dense>
          <v-col cols="6">
            <v-select
              v-model="suggestionMode"
              :items="suggestionModeOptions"
              hide-details
              label="Suggestion Mode"
            />
          </v-col>
          <v-col cols="6">
            <v-select
              v-model="suggestionType"
              :items="suggestionTypeOptions"
              hide-details
              label="Suggestion Type"
            />
          </v-col>
        </v-row>

        <v-row v-if="suggestionMode === SuggestionsMode.ON_DEMAND">
          <v-col>
            <v-btn
              color="primary"
              block
              :loading="onDemandSuggestionsLoading"
              @click="handleSuggestForSelectedRows"
            >
              Suggest for Selected Rows
            </v-btn>
          </v-col>
        </v-row> -->



        <!-- <v-row v-if="hasSuggestions && selectedAiOption === 'by_sample_type'">
          <v-col class="py-0">
            <div class="d-flex justify-space-between align-center">
              <div class="text-body-1 font-weight-medium">
                All Suggestions
              </div>
              <div>
                <v-tooltip>
                  <template #activator="{ props: activatorProps }">
                    <v-btn
                      variant="text"
                      density="comfortable"
                      color="primary"
                      icon
                      v-bind="activatorProps"
                      @click="handleRejectAllSuggestions"
                    >
                      <v-icon>
                        mdi-close
                      </v-icon>
                    </v-btn>
                  </template>
                  <span>Reject all suggestions</span>
                </v-tooltip>

                <v-tooltip>
                  <template #activator="{ props: activatorProps }">
                    <v-btn
                      variant="text"
                      density="comfortable"
                      color="primary"
                      icon
                      v-bind="activatorProps"
                      @click="handleAcceptAllSuggestions"
                    >
                      <v-icon>
                        mdi-check
                      </v-icon>
                    </v-btn>
                  </template>
                  <span>Accept all suggestions that apply to specific cells</span>
                </v-tooltip>
              </div>
            </div>
          </v-col>
        </v-row> -->




        <v-row v-if="selectedAiOption === 'by_sample_type'">
          <v-col>
            <div
              v-if="visibleGroups.length === 0"
              class="text--disabled"
            >
              No suggestions available.
            </div>
            <v-expansion-panels
                        v-else
                        variant="accordion"
                        class="mx-n2"
            >
              <v-expansion-panel
                v-for="group in visibleGroups"
                :key="group.label"
              >
                <v-expansion-panel-title>
                  <div class="d-flex align-center justify-space-between w-100 pr-2">
                    <span class="font-weight-medium">{{ group.label }}</span>
                    <v-chip
                      size="x-small"
                      color="primary"
                      variant="tonal"
                    >
                      {{ group.suggestions.length }} suggestion{{ group.suggestions.length !== 1 ? 's' : '' }}
                    </v-chip>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="pa-0">
                  <div
                    v-for="suggestion in group.suggestions"
                    :key="getSuggestionKey(suggestion)"
                  >
                    <v-card
                      class="mb-2"
                      elevation="1"
                      density="default"
                      :color="suggestion.is_ai_generated ? AI_SUGGESTION_BG : undefined"
                      @mouseenter="handleSuggestionHover(suggestion)"
                      @mouseleave="handleSuggestionLeave"
                    >
                      <v-card-text class="pa-2">
                        <div class="text-body-2">
                          <div
                            class="d-flex align-baseline mb-1 text-blue-darken-4 font-weight-medium"
                          >
                            <v-icon size="x-small" class="mr-1">mdi-creation</v-icon>
                            AI Suggested
                          </div>
                          <div v-if="suggestion.row !== null">
                            <span class="font-weight-medium">Row:</span> {{ suggestion.row + 1 }}
                          </div>
                          <div>
                            <span class="font-weight-medium">Column:</span> {{ getSlotTitle(suggestion.slot) }}
                          </div>
                          <div v-if="suggestion.source" class="text-caption text-medium-emphasis mt-1">
                            {{ suggestion.source }}
                          </div>
                        </div> 
                        <div class="d-flex flex-wrap align-center justify-end mt-1">
                          <div class="flex-grow-1">
                            <span
                              v-if="suggestion.current_value"
                              class="value previous"
                              v-text="suggestion.current_value"
                            />
                            <span
                              v-if="suggestion.value"
                              class="value suggested"
                              v-text="suggestion.value"
                            />
                          </div>
                          <v-btn
                            size="x-small"
                            variant="text"
                            icon
                            color="primary"
                            @click="handleJumpToCell(suggestion)"
                          >
                            <v-icon>mdi-target</v-icon>
                          </v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </div>
                  <div class="d-flex justify-end mt-1 mb-2">
                    <v-btn
                      size="small"
                      variant="text"
                      color="grey"
                      @click="handleDismissGroup(group.label)"
                    >
                      Dismiss all
                    </v-btn>
                    <v-btn
                      size="small"
                      variant="text"
                      color="primary"
                      @click="handleAcceptGroup(group)"
                    >
                      Accept all
                    </v-btn>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-col>
        </v-row>

        <v-row v-if="selectedAiOption !== 'by_sample_type'">
          <v-col>
            <div
              v-if="selectedAiOption !== null && !hasSuggestions"
              class="text--disabled"
            >
              No suggestions available.
            </div>

            <!-- <div
              v-if="hasSuggestions"
              class="d-flex justify-end mb-2"
            >
              <v-btn
                size="small"
                variant="text"
                color="grey"
                @click="handleRejectAllSuggestions"
              >
                Reject all
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                color="primary"
                @click="handleAcceptAllSuggestions"
              > 
                Accept all
              </v-btn>
            </div> -->


            <div
              v-for="suggestion in pendingSuggestions"
              :key="getSuggestionKey(suggestion)"
            >
              <v-card
                class="mb-4 mx-n2"
                elevation="2"
                density="default"
                :color="suggestion.is_ai_generated ? AI_SUGGESTION_BG : undefined"
                @mouseenter="handleSuggestionHover(suggestion)"
                @mouseleave="handleSuggestionLeave()"
              >
                <v-card-text class="pa-2">
                  <div class="flex-grow-1 full-width">
                    <div class="text-body-2">
                      <div
                        v-if="suggestion.is_ai_generated"
                        class="d-flex justify-space-between align-center mb-1 text-blue-darken-4 font-weight-medium"
                      >
                        <div class="d-flex align-baseline">
                          <v-icon
                            size="x-small"
                            class="mr-1"
                          >
                            mdi-creation
                          </v-icon>
                          AI Suggested
                        </div>
                        <v-tooltip max-width="500px">
                          <template #activator="{ props: activatorProps }">
                            <v-icon
                              size="small"
                              color="blue-darken-4"
                              v-bind="activatorProps"
                            >
                              mdi-information-outline
                            </v-icon>
                          </template>
                          <span>AI recommends areas of interest based on the content of the submission summary. To dismiss, select the X to remove it.</span>
                        </v-tooltip>
                      </div>
                      <div v-if="suggestion.row !== null">
                        <span class="font-weight-medium">Row:</span> {{ suggestion.row + 1 }}
                      </div>
                      <div>
                        <span class="font-weight-medium">Column:</span> {{ getSlotTitle(suggestion.slot) }}
                      </div>
                      <div v-if="suggestion.source">
                        <span class="font-weight-medium">Source:</span> {{ suggestion.source }}
                      </div>
                    </div>
                  </div>

                  <div class="d-flex flex-wrap align-center justify-end">
                    <div class="flex-grow-1">
                      <span
                        v-if="suggestion.current_value"
                        class="value previous"
                        v-text="suggestion.current_value"
                      />
                      <span
                        v-if="suggestion.value"
                        class="value suggested"
                        v-text="suggestion.value"
                      />
                    </div>

                    <div class="flex-shrink-0 flex-grow-0">
                      <v-tooltip>
                        <template #activator="{ props: activatorProps }">
                          <v-btn
                            variant="text"
                            density="comfortable"
                            icon
                            color="primary"
                            v-bind="activatorProps"
                            @click="handleJumpToCell(suggestion)"
                          >
                            <v-icon>
                              mdi-target
                            </v-icon>
                          </v-btn>
                        </template>
                        <span>Jump to cell</span>
                      </v-tooltip>

                      <v-tooltip>
                        <template #activator="{ props: activatorProps }">
                          <v-btn
                            variant="text"
                            density="comfortable"
                            icon
                            color="primary"
                            v-bind="activatorProps"
                            @click="handleRejectSuggestion(suggestion)"
                          >
                            <v-icon>
                              mdi-close
                            </v-icon>
                          </v-btn>
                        </template>
                        <span>Reject suggestion</span>
                      </v-tooltip>

                      <v-tooltip
                        v-if="canAcceptSuggestion(suggestion)"
                      >
                        <template #activator="{ props: activatorProps }">
                          <v-btn
                            variant="text"
                            density="comfortable"
                            icon
                            color="primary"
                            v-bind="activatorProps"
                            @click="handleAcceptSuggestion(suggestion)"
                          >
                            <v-icon>
                              mdi-check
                            </v-icon>
                          </v-btn>
                        </template>
                        <span>Accept suggestion</span>
                      </v-tooltip>
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </div>
            <div 
              v-if="hasSuggestions"
              class="d-flex justify-end mt-1"
            >
              <v-btn 
                size="small"
                variant="text"
                color="grey"
                @click="handleRejectAllSuggestions"
              >
                Reject all
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                color="primary"
                @click="handleAcceptAllSuggestions"
              >
                Accept all
              </v-btn>
            </div> 
          </v-col>
        </v-row>

        <v-row v-if="rejectedSuggestions.length > 0">
          <v-col>
            <v-btn
              color="grey"
              variant="outlined"
              small
              block
              @click="handleResetRejectedSuggestions"
            >
              Reset rejected suggestions
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-text v-else>
        Suggestions are disabled because you do not have permission to edit the metadata.
      </v-card-text>
    </v-defaults-provider>
  </v-card>
</template>

<style lang="scss" scoped>
.value {
  padding: 0.2rem;
  display: inline-block;
  border-radius: 2px;
  margin-right: 0.2rem;

  &.suggested {
    background-color: lightgreen;
    color: green;
  }

  &.previous {
    background-color: lightpink;
    color: red;
    text-decoration: line-through;
  }
}
</style>
