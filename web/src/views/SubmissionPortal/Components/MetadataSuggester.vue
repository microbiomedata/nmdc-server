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

const displayFilter = ref<string | null>(null);
const suggestionStarted = ref(false);

const filterOptions = [
  { label: 'By Row', value: 'by_row' },
  { label: 'By Column', value: 'by_column' },
];

const allMockSuggestions: MetadataSuggestion[] = [
  {
    type: 'replace', 
    row: 0,
    slot: 'elev',
    value: '278.3',
    current_value: '325',
    is_ai_generated: false,
    source: null,
  },
  {
    type: 'add',
    row: 1,
    slot: 'depth',
    value: '0.15',
    current_value: null,
    is_ai_generated: false,
    source: null,
  },
  {
    type: 'add', 
    row: 1,
    slot: 'env_broad_scale',
    value: 'temperate woodland biome [ENVO:01000221]',
    current_value: null,
    is_ai_generated: false,
    source: null,
  },
  {
    type: 'add', 
    row: 2,
    slot: 'env_broad_scale',
    value: 'temperate woodland biome [ENVO:01000221]',
    current_value: null,
    is_ai_generated: false,
    source: null,
  },
  {
    type: 'add', 
    row: 3,
    slot: 'env_broad_scale',
    value: 'temperate woodland biome [ENVO:01000221]',
    current_value: null,
    is_ai_generated: false,
    source: null,
  },
  {
    type: 'add', 
    row: 6,
    slot: 'env_broad_scale',
    value: 'temperate woodland biome [ENVO:01000221]',
    current_value: null,
    is_ai_generated: false,
    source: null,
  },
  {
    type: 'add', 
    row: 0,
    slot: 'env_broad_scale',
    value: 'temperate woodland biome [ENVO:01000221]',
    current_value: null,
    is_ai_generated: false,
    source: null,
  },
  {
    type: 'attention',
    row: null,
    slot: 'ecosystem',
    value: 'Environmental',
    current_value: 'null',
    is_ai_generated: true,
    source: "Based on the study description, samples were collected from an environmental ecosystem. 'Environmental' is the recommended broad ecosystem classification for this context.",
  },
  {
    type: 'add',
    row: null,
    slot: 'env_broad_scale',
    value: 'temperate woodland biome [ENVO:01000221]',
    current_value: null,
    is_ai_generated: true,
    source: "Based on the study description, samples were collected from a temperate woodland biome. This is the recommended broad scale environment classification for this context.",
  },
];

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

const filteredSuggestions = computed(() => {
  if (displayFilter.value === 'by_row') {
    return pendingSuggestions.value.filter((s) => s.row !== null);
  }
  if (displayFilter.value === 'by_column') {
    return pendingSuggestions.value.filter((s) => s.row === null);
  }
  return pendingSuggestions.value;
});

interface SuggestionCluster {
  key: string;
  suggestions: MetadataSuggestion[];
  isCollapsible: boolean;
}

const groupedFilteredSuggestions = computed<SuggestionCluster[]>(() => {
  const groups = new Map<string, MetadataSuggestion[]>();
  filteredSuggestions.value.forEach((s) => {
    // column level suggestions (row = null) always stand alone 
    const key = s.row === null ? getSuggestionKey(s) : `${s.slot}__${s.value}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(s);
  });
  return [...groups.entries()].map(([key, suggestions]) => ({
    key,
    suggestions,
    isCollapsible: suggestions.length > 1,
  }));
});

const expandedGroups = ref<string[]>([]);

function toggleGroup(key: string) {
  const idx = expandedGroups.value.indexOf(key);
  if(idx >= 0) {
    expandedGroups.value.splice(idx, 1);
  } else {
    expandedGroups.value.push(key);
  }
}

function formatRowRanges(suggestions: MetadataSuggestion[]): string {
  const rows = suggestions.map((s) => s.row!).sort((a, b) => a - b);
  const ranges: string[] = [];
  let start = rows[0];
  let end = rows[0];
  for (let i = 1; i < rows.length; i++) {
    if (rows[i] === end + 1) {
      end = rows[i];
    } else {
      ranges.push(start === end ? `${start + 1}` : `${start + 1}-${end + 1}`);
      start = rows[i];
      end = rows[i]; 
    }
  }
  ranges.push(start === end ? `${start + 1}` : `${start + 1}-${end + 1}`);
  return `Row${rows.length > 1 ? 's' : ''} ${ranges.join(', ')}`;
}

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
  acceptSuggestions(filteredSuggestions.value.filter(canAcceptSuggestion));
}

/**
 * Handle clicking the reject all button.
 */
function handleRejectAllSuggestions() {
  rejectSuggestions(filteredSuggestions.value);
}

/**
 * Handle clicking the "Suggest for Selected Rows" button.
 *
 * This will get the data for the selected rows, send it to the backend to get suggestions, and then add the
 * suggestions to the store.
 */
function handleStartSuggestion() {
  metadataSuggestions.value = allMockSuggestions;
  suggestionStarted.value = true;
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
            <v-btn
              color="primary"
              block
              @click="handleStartSuggestion"
            >
              <v-icon
                v-if="suggestionStarted"
                start
              >
                mdi-refresh
              </v-icon>
              Suggest Metadata
            </v-btn>
          </v-col>
        </v-row>
          <v-row v-if="!suggestionStarted">
            <v-col>
              <p class="text-body-2 text-medium-emphasis mb-1">
                Click <strong>Suggest Metadata</strong> to get suggestions for metadata values based on the content of the submission summary and any metadata you've already entered. Suggestions can be accepted or rejected, and will be hidden if rejected, but can be reset if you change your mind. You can re-run suggestions at any time as you add/edit your data.
              </p>
            </v-col>
          </v-row>

        <v-row v-if="suggestionStarted">
          <v-col>
            <v-select
              v-model="displayFilter"
              :items="filterOptions"
              item-title="label"
              item-value="value"
              label="Group by"
              hide-details
              clearable
            />
          </v-col>
        </v-row>

        <v-row v-if="suggestionStarted">
          <v-col>
            <div
              v-if="filteredSuggestions.length === 0"
              class="text--disabled"
            >
              No suggestions available.
            </div>

            <div
              v-if="filteredSuggestions.length > 0"
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
            </div>

            <div
              v-for="cluster in groupedFilteredSuggestions"
              :key="cluster.key"
            >
              <!-- collapsed cluster - multiple rows, same slot and value -->
              <v-card
                v-if="cluster.isCollapsible"
                class="mb-4 mx-n2"
                elevation="2"
              >
                <v-card-text class="pa-2">
                  <div class="d-flex align-center justify-space-between">
                    <div class="d-flex align-center flex-wrap ga-1">
                      <v-chip size="small" color="primary" variant="tonal">
                        {{ formatRowRanges(cluster.suggestions) }}
                      </v-chip>
                      <span class="text-body-2 font-weight-medium">
                        {{ getSlotTitle(cluster.suggestions[0].slot) }}
                      </span>
                      <span
                        v-if="cluster.suggestions[0].value"
                        class="value suggested"
                        v-text="cluster.suggestions[0].value"
                      />
                    </div>
                    <div class="d-flex align-center flex-shrink-0">
                      <v-btn
                        variant="text"
                        density="comfortable"
                        icon
                        @click="toggleGroup(cluster.key)"
                      >
                        <v-icon>
                          {{ expandedGroups.includes(cluster.key) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                        </v-icon>
                      </v-btn>
                      <v-tooltip>
                        <template #activator="{ props: activatorProps }">
                          <v-btn
                            variant="text"
                            density="comfortable"
                            icon
                            color="primary"
                            v-bind="activatorProps"
                            @click="rejectSuggestions(cluster.suggestions)"
                          >
                            <v-icon>mdi-close</v-icon>
                          </v-btn>
                        </template>
                        <span>Reject all {{ cluster.suggestions.length }} suggestions</span>
                      </v-tooltip>
                      <v-tooltip>
                        <template #activator="{ props: activatorProps }">
                          <v-btn
                            variant="text"
                            density="comfortable"
                            icon
                            color="primary"
                            v-bind="activatorProps"
                            @click="acceptSuggestions(cluster.suggestions.filter(canAcceptSuggestion))"
                          >
                            <v-icon>mdi-check</v-icon>
                          </v-btn>
                        </template>
                        <span>Accept all {{ cluster.suggestions.length }} suggestions</span>
                      </v-tooltip>
                    </div>
                  </div>
                  <div
                    v-if="expandedGroups.includes(cluster.key)"
                    class="mt-2"
                  >
                    <v-divider class="mb-1" />
                    <div
                      v-for="s in cluster.suggestions"
                      :key="getSuggestionKey(s)"
                      class="d-flex align-center justify-space-between py-1"
                      @mouseenter="handleSuggestionHover(s)"
                      @mouseleave="handleSuggestionLeave()"
                    >
                      <span class="text-body-2">Row {{ s.row! + 1 }}</span>
                      <div class="d-flex align-center">
                        <v-tooltip>
                          <template #activator="{ props: activatorProps }">
                            <v-btn
                              variant="text"
                              density="comfortable"
                              icon
                              size="small"
                              color="primary"
                              v-bind="activatorProps"
                              @click="handleRejectSuggestion(s)"
                            >
                              <v-icon size="small">mdi-close</v-icon>
                            </v-btn>
                          </template>
                          <span>Reject row {{ s.row! + 1 }}</span>
                        </v-tooltip>
                        <v-tooltip v-if="canAcceptSuggestion(s)">
                          <template #activator="{ props: activatorProps }">
                            <v-btn
                              variant="text"
                              density="comfortable"
                              icon
                              size="small"
                              color="primary"
                              v-bind="activatorProps"
                              @click="handleAcceptSuggestion(s)"
                            >
                              <v-icon size="small">mdi-check</v-icon>
                            </v-btn>
                          </template>
                          <span>Accept row {{ s.row! + 1 }}</span>
                        </v-tooltip>
                      </div>
                    </div>   
                  </div>
                </v-card-text>
              </v-card>

              <!-- Single suggestion (row-specific or column-level) -->
              <v-card
                v-else
                class="mb-4 mx-n2"
                elevation="2"
                density="default"
                :color="cluster.suggestions[0].is_ai_generated ? AI_SUGGESTION_BG : undefined"
                @mouseenter="handleSuggestionHover(cluster.suggestions[0])"
                @mouseleave="handleSuggestionLeave()"
              >
                <v-card-text class="pa-2">
                  <div class="flex-grow-1 full-width">
                    <div class="text-body-2">
                      <div
                        v-if="cluster.suggestions[0].is_ai_generated"
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
                      <div v-if="cluster.suggestions[0].row !== null">
                        <span class="font-weight-medium">Row:</span> {{ cluster.suggestions[0].row + 1 }}
                      </div>
                      <div>
                        <span class="font-weight-medium">Column:</span> {{ getSlotTitle(cluster.suggestions[0].slot) }}
                      </div>
                      <div v-if="cluster.suggestions[0].source">
                        <span class="font-weight-medium">Source:</span> {{ cluster.suggestions[0].source }}
                      </div>
                    </div>
                  </div>

                  <div class="d-flex flex-wrap align-center justify-end">
                    <div class="flex-grow-1">
                      <span
                        v-if="cluster.suggestions[0].current_value"
                        class="value previous"
                        v-text="cluster.suggestions[0].current_value"
                      />
                      <span
                        v-if="cluster.suggestions[0].value"
                        class="value suggested"
                        v-text="cluster.suggestions[0].value"
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
                            @click="handleJumpToCell(cluster.suggestions[0])"
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
                            @click="handleRejectSuggestion(cluster.suggestions[0])"
                          >
                            <v-icon>
                              mdi-close
                            </v-icon>
                          </v-btn>
                        </template>
                        <span>Reject suggestion</span>
                      </v-tooltip>

                      <v-tooltip
                        v-if="canAcceptSuggestion(cluster.suggestions[0])"
                      >
                        <template #activator="{ props: activatorProps }">
                          <v-btn
                            variant="text"
                            density="comfortable"
                            icon
                            color="primary"
                            v-bind="activatorProps"
                            @click="handleAcceptSuggestion(cluster.suggestions[0])"
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
