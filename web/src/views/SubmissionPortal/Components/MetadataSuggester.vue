<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import { groupBy } from 'lodash';
import {
  metadataSuggestions,
  suggestionMode,
  suggestionType,
} from '@/views/SubmissionPortal/store';
import { SuggestionsMode, SuggestionType } from '@/views/SubmissionPortal/types';

const suggestionModeOptions = Object.values(SuggestionsMode);
const suggestionTypeOptions = Object.values(SuggestionType);

export default defineComponent({
  setup() {
    const suggestionsByRow = computed(() => groupBy(metadataSuggestions.value, 'row'));

    return {
      suggestionModeOptions,
      suggestionMode,
      suggestionTypeOptions,
      suggestionType,
      suggestionsByRow,
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

      <v-row>
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

      <div v-if="Object.keys(suggestionsByRow).length === 0">
        No suggestions available.
      </div>

      <div
        v-for="(suggestion, row) in suggestionsByRow"
        :key="row"
        class="mt-4"
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
                @click="$emit('jump-to-cell', row, s.slot)"
              >
                <v-icon>
                  mdi-target
                </v-icon>
              </v-btn>
              <v-btn
                icon
                color="primary"
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
