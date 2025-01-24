<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  ref,
} from '@vue/composition-api';
import { groupBy } from 'lodash';
import {
  metadataSuggestions,
  suggestionMode,
  suggestionType,
} from '@/views/SubmissionPortal/store';
import { MetadataSuggestion, SuggestionsMode, SuggestionType } from '@/views/SubmissionPortal/types';
import type { HarmonizerApi } from '@/views/SubmissionPortal/harmonizerApi';
import { getRejectedSuggestions, setRejectedSuggestions } from '@/store/localStorage';

const suggestionModeOptions = Object.values(SuggestionsMode);
const suggestionTypeOptions = Object.values(SuggestionType);

function getSuggestionKey(suggestion: MetadataSuggestion) {
  return `${suggestion.row}__${suggestion.slot}__${suggestion.value}`;
}

export default defineComponent({
  props: {
    harmonizerApi: {
      type: Object as PropType<HarmonizerApi>,
      required: true,
    },
  },

  setup({ harmonizerApi }) {
    const rejectedSuggestions = ref(getRejectedSuggestions());

    const displaySuggestions = computed(() => {
      const filteredSuggestions = metadataSuggestions.value.filter((suggestion) => {
        const key = getSuggestionKey(suggestion);
        return !rejectedSuggestions.value.includes(key);
      });
      return groupBy(filteredSuggestions, 'row');
    });

    function handleJumpToCell(suggestion: MetadataSuggestion) {
      const { row, slot } = suggestion;
      const col = harmonizerApi.slotColumns[slot];
      harmonizerApi.jumpToRowCol(row, col);
    }

    function handleRejectSuggestion(suggestion: MetadataSuggestion) {
      const key = getSuggestionKey(suggestion);
      rejectedSuggestions.value.push(key);
      setRejectedSuggestions(rejectedSuggestions.value);
    }

    return {
      handleJumpToCell,
      handleRejectSuggestion,
      rejectedSuggestions,
      SuggestionsMode,
      suggestionModeOptions,
      suggestionMode,
      suggestionTypeOptions,
      suggestionType,
      suggestionsByRow: displaySuggestions,
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
        z-index="400"
      >
        <span>
          As you enter sample metadata, the Metadata Suggester will offer suggestions for metadata values based on the
          metadata values you have already entered.
        </span>
        <template #activator="{ on, attrs }">
          <v-icon
            v-bind="attrs"
            v-on="on"
          >
            mdi-information-outline
          </v-icon>
        </template>
      </v-tooltip>
    </v-card-title>

    <v-container>
      <v-row dense>
        <v-col cols="6">
          <v-select
            v-model="suggestionMode"
            :items="suggestionModeOptions"
            dense
            hide-details
            label="Suggestion Mode"
            outlined
          />
        </v-col>
        <v-col cols="6">
          <v-select
            v-model="suggestionType"
            :items="suggestionTypeOptions"
            dense
            hide-details
            label="Suggestion Type"
            outlined
          />
        </v-col>
      </v-row>

      <v-row v-if="suggestionMode === SuggestionsMode.ON_DEMAND">
        <v-col>
          <v-btn
            color="primary"
            block
          >
            Suggest for Selected Row(s)
          </v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col>
          <v-btn
            class="rounded-r-0"
            color="primary"
            outlined
          >
            <v-icon>
              mdi-close
            </v-icon>
          </v-btn>
          <v-btn
            class="rounded-l-0"
            style="border-left-width: 0"
            color="primary"
            outlined
          >
            <v-icon>
              mdi-check
            </v-icon>
          </v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col>
          <div
            v-if="Object.keys(suggestionsByRow).length === 0"
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
              elevation="0"
              rounded
              outlined
            >
              <div
                v-for="s in suggestion"
                :key="s.slot"
                class="ma-2 d-flex flex-wrap justify-end"
              >
                <div class="flex-grow-1 full-width">
                  <div
                    class="text-body-2"
                  >
                    <span class="grey--text">Column:</span> {{ s.slot }}
                  </div>
                  <div>
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
                </div>
                <div
                  class="flex-shrink-0 flex-grow-0"
                >
                  <v-btn
                    icon
                    color="primary"
                    @click="handleJumpToCell(s)"
                  >
                    <v-icon>
                      mdi-target
                    </v-icon>
                  </v-btn>
                  <v-btn
                    icon
                    color="primary"
                    @click="handleRejectSuggestion(s)"
                  >
                    <v-icon>
                      mdi-close
                    </v-icon>
                  </v-btn>
                  <v-btn
                    icon
                    color="primary"
                  >
                    <v-icon>
                      mdi-check
                    </v-icon>
                  </v-btn>
                </div>
              </div>
            </v-sheet>
          </div>
        </v-col>
      </v-row>
    </v-container>
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
