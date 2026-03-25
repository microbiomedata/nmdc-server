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
  SuggestionType,
} from '@/views/SubmissionPortal/types';
import type HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi';
import { getRejectedSuggestions, setRejectedSuggestions } from '@/store/localStorage';
import { useRoute } from 'vue-router';
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

const suggestionModeOptions = Object.values(SuggestionsMode);
const suggestionTypeOptions = Object.values(SuggestionType);

function getSuggestionKey(suggestion: MetadataSuggestion) {
  return `${suggestion.row}__${suggestion.slot}__${suggestion.value}`;
}

const props = defineProps<MetadataSuggesterProps>();

const route = useRoute();
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
    await fetchSuggestionsFromSampleRows((route.params as { id: string }).id, props.schemaClassName, changedRowData);
  } finally {
    onDemandSuggestionsLoading.value = false;
  }
}

/**
 * Handle resetting the rejected suggestions list.
 */
function handleResetRejectedSuggestions() {
  rejectedSuggestions.value = [];
  setRejectedSuggestions((route.params as { id: string }).id, props.schemaClassName, rejectedSuggestions.value);
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
        </v-row>

        <v-row v-if="hasSuggestions">
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
        </v-row>

        <v-row>
          <v-col>
            <div
              v-if="!hasSuggestions"
              class="text--disabled"
            >
              No suggestions available.
            </div>

            <div
              v-for="suggestion in pendingSuggestions"
              :key="getSuggestionKey(suggestion)"
            >
              <v-card
                class="mb-4 mx-n2"
                elevation="2"
                density="default"
                :color="suggestion.is_ai_generated ? AI_SUGGESTION_BG : undefined"
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
