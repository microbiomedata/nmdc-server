<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  ref,
  watchEffect,
} from 'vue';
import { groupBy } from 'lodash';
import {
  addMetadataSuggestions,
  removeMetadataSuggestions,
  metadataSuggestions,
  suggestionMode,
  suggestionType,
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

const suggestionModeOptions = Object.values(SuggestionsMode);
const suggestionTypeOptions = Object.values(SuggestionType);

function getSuggestionKey(suggestion: MetadataSuggestion) {
  return `${suggestion.row}__${suggestion.slot}__${suggestion.value}`;
}

/**
 * Component to display metadata suggestions and allow users to accept or reject them.
 */
export default defineComponent({
  props: {
    /**
     * Whether the suggester UI is displayed or not. If false, the component will display a message indicating that
     * the user does not have permission to edit the metadata.
     */
    enabled: {
      type: Boolean,
      required: true,
    },
    /**
     * The Harmonizer API instance.
     */
    harmonizerApi: {
      type: Object as PropType<HarmonizerApi>,
      required: true,
    },
    /**
     * The schema class name for the active template.
     */
    schemaClassName: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const route = useRoute();
    const rejectedSuggestions = ref([] as string[]);
    const onDemandSuggestionsLoading = ref(false);

    // When the route or schema class name changes (because of changing the active template tab), update the rejected
    // suggestions list from local storage.
    watchEffect(() => {
      rejectedSuggestions.value = getRejectedSuggestions((route.params as { id: string }).id, props.schemaClassName);
    });

    // Filter out rejected suggestions and group by row
    const suggestionsByRow = computed(() => {
      const filteredSuggestions = metadataSuggestions.value.filter((suggestion) => {
        const key = getSuggestionKey(suggestion);
        return !rejectedSuggestions.value.includes(key);
      });
      return groupBy(filteredSuggestions, 'row');
    });

    const hasSuggestions = computed(() => Object.keys(suggestionsByRow.value).length > 0);

    /**
     * Accepts the given suggestions by setting the cell data via the Harmonizer API and removing the suggestions from
     * the store.
     * @param suggestions
     */
    function acceptSuggestions(suggestions: MetadataSuggestion[]) {
      const cellData = [] as CellData[];
      suggestions.forEach((suggestion) => {
        const { row, slot } = suggestion;
        const col = props.harmonizerApi.slotInfo.get(slot)?.columnIndex;
        if (col === undefined) {
          return;
        }
        cellData.push({ row, col, text: suggestion.value });
      });

      // Do this outside of the forEach so that the DataHarmonizer afterChange hook is only triggered once
      props.harmonizerApi.setCellData(cellData);

      removeMetadataSuggestions((route.params as { id: string }).id, props.schemaClassName, suggestions);
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
      setRejectedSuggestions((route.params as { id: string }).id, props.schemaClassName, rejectedSuggestions.value);
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
      props.harmonizerApi.jumpToRowCol(row, col);
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
     * Handle clicking the accept all button.
     */
    function handleAcceptAllSuggestions() {
      acceptSuggestions(Object.values(suggestionsByRow.value).flat());
    }

    /**
     * Handle clicking the reject all button.
     */
    function handleRejectAllSuggestions() {
      rejectSuggestions(Object.values(suggestionsByRow.value).flat());
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
        for (let i = range[0]; i && range[2] && i <= range[2]; i += 1) {
          acc.push(i);
        }
        return acc;
      }, [] as number[]);
      const changedRowData = props.harmonizerApi.getDataByRows(rows);
      try {
        await addMetadataSuggestions((route.params as { id: string }).id, props.schemaClassName, changedRowData);
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

    return {
      SuggestionsMode,
      getSlotTitle,
      handleAcceptAllSuggestions,
      handleAcceptSuggestion,
      handleJumpToCell,
      handleRejectAllSuggestions,
      handleRejectSuggestion,
      handleResetRejectedSuggestions,
      handleSuggestForSelectedRows,
      hasSuggestions,
      onDemandSuggestionsLoading,
      rejectedSuggestions,
      suggestionMode,
      suggestionModeOptions,
      suggestionType,
      suggestionTypeOptions,
      suggestionsByRow,
      TOOLTIP_DELAY: '600',
    };
  },
});
</script>

<template>
  <v-card elevation="0">
    <v-card-title>
      Metadata Suggester
      <v-spacer />
      <v-tooltip
        bottom
        min-width="300px"
        max-width="600px"
        :open-delay="TOOLTIP_DELAY"
        z-index="400"
      >
        <span>
          As you enter sample metadata, the Metadata Suggester will offer suggestions for metadata values based on the
          metadata values you have already entered.
        </span>
        <template #activator="{ props }">
          <v-icon
            v-bind="props"
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
            dense
            hide-details
            label="Suggestion Mode"
            variant="outlined"
          />
        </v-col>
        <v-col cols="6">
          <v-select
            v-model="suggestionType"
            :items="suggestionTypeOptions"
            dense
            hide-details
            label="Suggestion Type"
            variant="outlined"
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
        <v-col>
          <div class="d-flex justify-space-between align-center">
            <div class="text-body-1 text--primary font-weight-medium">
              All Suggestions
            </div>
            <div>
              <v-tooltip
                bottom
                :open-delay="TOOLTIP_DELAY"
              >
                <template #activator="{ props }">
                  <v-btn
                    color="primary"
                    icon
                    v-bind="props"
                    @click="handleRejectAllSuggestions"
                  >
                    <v-icon>
                      mdi-close
                    </v-icon>
                  </v-btn>
                </template>
                <span>Reject all suggestions</span>
              </v-tooltip>

              <v-tooltip
                bottom
                :open-delay="TOOLTIP_DELAY"
              >
                <template #activator="{ props }">
                  <v-btn
                    color="primary"
                    icon
                    v-bind="props"
                    @click="handleAcceptAllSuggestions"
                  >
                    <v-icon>
                      mdi-check
                    </v-icon>
                  </v-btn>
                </template>
                <span>Accept all suggestions</span>
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
            v-for="(suggestion, row) in suggestionsByRow"
            :key="row"
          >
            <div class="text-body-2">
              Row: {{ Number(row) + 1 }}
            </div>

            <v-sheet
              :key="row"
              class="mb-4"
              elevation="0"
              rounded
              variant="outlined"
            >
              <div
                v-for="s in suggestion"
                :key="s.slot"
                class="ma-2"
              >
                <div class="flex-grow-1 full-width">
                  <div class="text-body-2">
                    <span class="grey--text">Column:</span> {{ getSlotTitle(s.slot) }}
                  </div>
                </div>

                <div class="d-flex flex-wrap align-center justify-end">
                  <div class="flex-grow-1">
                    <span
                      v-if="s.current_value"
                      class="value previous"
                      v-text="s.current_value"
                    />
                    <span
                      class="value suggested"
                      v-text="s.value"
                    />
                  </div>

                  <div class="flex-shrink-0 flex-grow-0">
                    <v-tooltip
                      bottom
                      :open-delay="TOOLTIP_DELAY"
                    >
                      <template #activator="{ props }">
                        <v-btn
                          icon
                          color="primary"
                          v-bind="props"
                          @click="handleJumpToCell(s)"
                        >
                          <v-icon>
                            mdi-target
                          </v-icon>
                        </v-btn>
                      </template>
                      <span>Jump to cell</span>
                    </v-tooltip>

                    <v-tooltip
                      bottom
                      :open-delay="TOOLTIP_DELAY"
                    >
                      <template #activator="{ props }">
                        <v-btn
                          icon
                          color="primary"
                          v-bind="props"
                          @click="handleRejectSuggestion(s)"
                        >
                          <v-icon>
                            mdi-close
                          </v-icon>
                        </v-btn>
                      </template>
                      <span>Reject suggestion</span>
                    </v-tooltip>

                    <v-tooltip
                      bottom
                      :open-delay="TOOLTIP_DELAY"
                    >
                      <template #activator="{ props }">
                        <v-btn
                          icon
                          color="primary"
                          v-bind="props"
                          @click="handleAcceptSuggestion(s)"
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
              </div>
            </v-sheet>
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
