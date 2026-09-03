<script setup lang="ts">
/**
 * Component to display metadata suggestions and allow users to accept or reject them.
 */
import { computed, ref, watchEffect } from 'vue';
import {
  CellData,
  MetadataSuggestion,
  SuggestionFill,
  SuggestionType,
} from '@/views/SubmissionPortal/types';
import type HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi';
import { getRejectedSuggestions, setPendingSuggestions, setRejectedSuggestions } from '@/store/localStorage';
import { AI_SUGGESTION_BG } from '@/views/SubmissionPortal/colors.ts';
import { useSubmissionStore } from '../store';

interface MetadataSuggesterProps {
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

const store = useSubmissionStore();
const { loadSuggestionsFromSampleRows } = store;

const suggestionStarted = ref(false);

const scopeOptions = [
  { label: 'Suggest Fields', value: SuggestionFill.FIELD_SUGGESTION, tooltip: 'Highlights metadata fields that may be relevant to your submission, without suggesting specific values.' },
  { label: 'Suggest Values', value: SuggestionFill.VALUE_SUGGESTION, tooltip: 'Suggests specific values to fill into individual cells.' },
];
const suggestionTypeOptions = [
  { label: SuggestionType.ADDITIONS, value: SuggestionType.ADDITIONS, tooltip: 'Suggestions for empty cells only — no existing values will be overwritten.' },
  { label: SuggestionType.REPLACEMENTS, value: SuggestionType.REPLACEMENTS, tooltip: 'Suggestions that would replace an existing cell value with a new one.' },
];

const allFilterOptions = [
  ...suggestionTypeOptions,
  { type: 'divider' },
  ...scopeOptions,
];

const filterSelectionLabel = computed(() => {
  const fillsAll = store.ui.suggestionFills.size === 0 || store.ui.suggestionFills.size === scopeOptions.length;
  const typesAll = store.ui.suggestionTypes.size === 0 || store.ui.suggestionTypes.size === suggestionTypeOptions.length;
  if (fillsAll && typesAll) return 'All';
  const parts = [
    ...(typesAll ? [] : Array.from(store.ui.suggestionTypes).map((t) => suggestionTypeOptions.find((o) => o.value === t)?.label)),
    ...(fillsAll ? [] : Array.from(store.ui.suggestionFills).map((f) => scopeOptions.find((o) => o.value === f)?.label)),
  ].filter(Boolean);
  return parts.join(', ');
});

function onFilterUpdate(values: string[]) {
  store.ui.suggestionFills = new Set(
    values.filter((v): v is SuggestionFill => Object.values(SuggestionFill).includes(v as SuggestionFill)),
  );
  store.ui.suggestionTypes = new Set(
    values.filter((v): v is SuggestionType => Object.values(SuggestionType).includes(v as SuggestionType)),
  );
}

function getSuggestionKey(suggestion: MetadataSuggestion) {
  return `${suggestion.row}__${suggestion.slot}__${suggestion.value}`;
}

const props = defineProps<MetadataSuggesterProps>();
const emit = defineEmits<{
  'fetch-study-info-suggestions': [];
}>();

const rejectedSuggestions = ref([] as string[]);
const onDemandSuggestionsLoading = ref(false);

// When the route or schema class name changes (because of changing the active template tab), update the rejected
// suggestions list from local storage.
watchEffect(() => {
  if (store.sampleSet.record === null) {
    rejectedSuggestions.value = [];
    return;
  }
  rejectedSuggestions.value = getRejectedSuggestions(store.sampleSet.record.id, props.schemaClassName);
});

// Suggestions that have been neither accepted nor rejected.
const pendingSuggestions = computed(() => (
    store.sampleSet.suggestions
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

const filteredSuggestions = computed(() => {
  let suggestions = pendingSuggestions.value;
  // Scope filter: FIELD_SUGGESTION = slot suggestions (row === null), VALUE_SUGGESTION = value suggestions (row !== null)
  // Empty set means no filter applied (show all)
  const fills = store.ui.suggestionFills;
  if (fills.size > 0 && (!fills.has(SuggestionFill.FIELD_SUGGESTION) || !fills.has(SuggestionFill.VALUE_SUGGESTION))) {
    if (fills.has(SuggestionFill.VALUE_SUGGESTION)) {
      suggestions = suggestions.filter((s) => s.row !== null);
    } else {
      suggestions = suggestions.filter((s) => s.row === null);
    }
  }
  // Type filter — empty set means no filter applied (show all)
  const types = store.ui.suggestionTypes;
  if (types.size > 0 && (!types.has(SuggestionType.ADDITIONS) || !types.has(SuggestionType.REPLACEMENTS))) {
    if (types.has(SuggestionType.ADDITIONS)) {
      suggestions = suggestions.filter((s) => s.type === 'add');
    } else {
      suggestions = suggestions.filter((s) => s.type === 'replace');
    }
  }
  return suggestions;
});

interface SuggestionCluster {
  key: string;
  suggestions: MetadataSuggestion[];
  firstSuggestion: MetadataSuggestion;
  isCollapsible: boolean;
}

const groupedFilteredSuggestions = computed<SuggestionCluster[]>(() => {
  const groups = new Map<string, MetadataSuggestion[]>();
  filteredSuggestions.value.forEach((s) => {
    // Group row-level suggestions by slot+value so identical suggestions across multiple rows collapse into one card.
    // Column-level suggestions (row === null) always stand alone.
    const key = s.row === null ? getSuggestionKey(s) : `${s.slot}__${s.value}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(s);
  });
  return [...groups.entries()].map(([key, suggestions]) => ({
    key,
    suggestions,
    firstSuggestion: suggestions[0]!,
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
  let start = rows[0]!;
  let end = rows[0]!;
  for (let i = 1; i < rows.length; i++) {
    if (rows[i]! === end + 1) {
      end = rows[i]!;
    } else {
      ranges.push(start === end ? `${start + 1}` : `${start + 1}-${end + 1}`);
      start = rows[i]!;
      end = rows[i]!;
    }
  }
  ranges.push(start === end ? `${start + 1}` : `${start + 1}-${end + 1}`);
  return `${ranges.join(', ')}`;
}

/**
 * Remove the given metadata suggestions from the list of pending suggestions. Then sync the pending suggestions with
 * local storage.
 *
 * @param schemaClassName
 * @param suggestions
 */
function removeMetadataSuggestions(schemaClassName: string, suggestions: MetadataSuggestion[]) {
  if (store.sampleSet.record === null) {
    return;
  }
  store.sampleSet.suggestions = store.sampleSet.suggestions.filter(
    (suggestion) => !suggestions.includes(suggestion),
  );

  setPendingSuggestions(store.sampleSet.record.id, schemaClassName, store.sampleSet.suggestions);
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

  // Do this outside of the forEach so that the DataHarmonizer afterChange hook is only triggered once.
  // Pass 'accept_suggestion' as the source so that the live-suggestion re-fetch is NOT triggered for these
  // programmatic changes — otherwise all pending suggestions for the affected row(s) would be cleared.
  props.harmonizerApi.setCellData(cellData, 'accept_suggestion');

  removeMetadataSuggestions(props.schemaClassName, suggestions);
}

/**
 * Rejects the given suggestions by adding them to the rejected suggestions list in local storage.
 * @param suggestions
 */
function rejectSuggestions(suggestions: MetadataSuggestion[]) {
  if (store.sampleSet.record === null) {
    return;
  }
  suggestions.forEach((suggestion) => {
    const key = getSuggestionKey(suggestion);
    rejectedSuggestions.value.push(key);
  });
  setRejectedSuggestions(store.sampleSet.record.id, props.schemaClassName, rejectedSuggestions.value);
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
 * Handle clicking the "Suggest Metadata" button.
 *
 * Fetches suggestions from study info, then marks suggestion as started.
 */
function handleStartSuggestion() {
  emit('fetch-study-info-suggestions');
  suggestionStarted.value = true;
}

async function _handleSuggestForSelectedRows() {
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
    await loadSuggestionsFromSampleRows(props.schemaClassName, changedRowData);
  } finally {
    onDemandSuggestionsLoading.value = false;
  }
}

/**
 * Handle resetting the rejected suggestions list.
 */
function handleResetRejectedSuggestions() {
  if (store.sampleSet.record === null) {
    return;
  }
  rejectedSuggestions.value = [];
  setRejectedSuggestions(store.sampleSet.record.id, props.schemaClassName, rejectedSuggestions.value);
}

/**
 * Translate a slot name to its title.
 * @param slot
 */
function getSlotTitle(slot: string) {
  return props.harmonizerApi.slotInfo.get(slot)?.title ?? slot;
}
</script>

<template>
  <v-card
    elevation="0"
    tile
    :loading="store.sampleSet.requests.loadingSuggestions.loading"
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
              :model-value="[...Array.from(store.ui.suggestionFills), ...Array.from(store.ui.suggestionTypes)]"
              :items="allFilterOptions"
              item-title="label"
              item-value="value"
              label="Filter"
              hide-details
              clearable
              persistent-placeholder
              multiple
              @update:model-value="onFilterUpdate"
            >
              <template #selection="{ index }">
                <span v-if="index === 0">
                  {{ filterSelectionLabel }}
                </span>
              </template>
              <template #item="{ item, props: itemProps }">
                <v-divider v-if="'type' in item.raw && item.raw.type === 'divider'" />
                <v-tooltip
                  v-else-if="'tooltip' in item.raw && item.raw.tooltip"
                  :text="(item.raw as { tooltip: string }).tooltip"
                  location="right"
                  max-width="260"
                  open-delay="300"
                >
                  <template #activator="{ props: tooltipProps }">
                    <v-list-item v-bind="{ ...itemProps, ...tooltipProps }" />
                  </template>
                </v-tooltip>
              </template>
            </v-select>
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
                :color="cluster.firstSuggestion.is_ai_generated ? AI_SUGGESTION_BG : undefined"
              >
                <v-card-text class="pa-2">
                  <div
                    v-if="cluster.firstSuggestion.is_ai_generated"
                    class="d-flex justify-space-between align-center mb-1 text-blue-darken-4 font-weight-medium"
                  >
                    <div
                      class=""
                      d-flex
                      align-baseline
                    >
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
                  <div class="d-flex align-center justify-space-between">
                    <!-- <div class="d-flex align-center flex-wrap ga-1"> -->
                    <div class="text-body-2">
                      <span class="font-weight-medium">Rows:</span>
                      {{ formatRowRanges(cluster.suggestions).replace(/^Rows?: /, '') }}
                    </div>
                    <!-- </div> -->
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
                            <v-icon>mdi-check-all</v-icon>
                          </v-btn>
                        </template>
                        <span>Accept all {{ cluster.suggestions.length }} suggestions</span>
                      </v-tooltip>
                    </div>
                  </div>
                  <div class="d-flex align-center flex-wrap ga-1 mt-1">
                    <span class="text-body-2">
                      <span class="font-weight-medium">Column:</span>
                      {{ getSlotTitle(cluster.firstSuggestion.slot) }}
                    </span>
                  </div>
                  <div v-if="cluster.firstSuggestion.source">
                    <span class="font-weight-medium">Reasoning:</span> {{ cluster.firstSuggestion.source }}
                  </div>
                  <span
                    v-if="cluster.firstSuggestion.value"
                    class="value suggested"
                    v-text="cluster.firstSuggestion.value"
                  />
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
                      <div class="flex-grow-1 mr-2">
                        <div class="text-body-2 font-weight-medium">
                          Row {{ s.row! + 1 }}
                        </div>
                      </div>
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
                              @click="handleJumpToCell(s)"
                            >
                              <v-icon size="small">
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
                              size="small"
                              color="primary"
                              v-bind="activatorProps"
                              @click="handleRejectSuggestion(s)"
                            >
                              <v-icon size="small">
                                mdi-close
                              </v-icon>
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
                              <v-icon size="small">
                                mdi-check
                              </v-icon>
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
                :color="cluster.firstSuggestion.is_ai_generated ? AI_SUGGESTION_BG : undefined"
                @mouseenter="handleSuggestionHover(cluster.firstSuggestion)"
                @mouseleave="handleSuggestionLeave()"
              >
                <v-card-text class="pa-2">
                  <div class="flex-grow-1 full-width">
                    <div class="text-body-2">
                      <div
                        v-if="cluster.firstSuggestion.is_ai_generated"
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
                      <div v-if="cluster.firstSuggestion.row !== null">
                        <span class="font-weight-medium">Row:</span> {{ cluster.firstSuggestion.row + 1 }}
                      </div>
                      <div>
                        <span class="font-weight-medium">Column:</span> {{ getSlotTitle(cluster.firstSuggestion.slot) }}
                      </div>
                      <div v-if="cluster.firstSuggestion.source">
                        <span class="font-weight-medium">Reasoning:</span> {{ cluster.firstSuggestion.source }}
                      </div>
                    </div>
                  </div>

                  <div class="d-flex flex-wrap align-center justify-end">
                    <div class="flex-grow-1">
                      <span
                        v-if="cluster.firstSuggestion.current_value"
                        class="value previous"
                        v-text="cluster.firstSuggestion.current_value"
                      />
                      <span
                        v-if="cluster.firstSuggestion.value"
                        class="value suggested"
                        v-text="cluster.firstSuggestion.value"
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
                            @click="handleJumpToCell(cluster.firstSuggestion)"
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
                            @click="handleRejectSuggestion(cluster.firstSuggestion)"
                          >
                            <v-icon>
                              mdi-close
                            </v-icon>
                          </v-btn>
                        </template>
                        <span>Reject suggestion</span>
                      </v-tooltip>

                      <v-tooltip
                        v-if="canAcceptSuggestion(cluster.firstSuggestion)"
                      >
                        <template #activator="{ props: activatorProps }">
                          <v-btn
                            variant="text"
                            density="comfortable"
                            icon
                            color="primary"
                            v-bind="activatorProps"
                            @click="handleAcceptSuggestion(cluster.firstSuggestion)"
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
