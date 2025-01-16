<script lang="ts">
import {
  defineComponent,
  computed,
  ref,
  watch,
  PropType,
} from '@vue/composition-api';
import type { Ref } from '@vue/composition-api';
import type { HarmonizerApi } from '../harmonizerApi';

type SearchResult = {
  row: number;
  col: number;
};

// Pressing "clear" button will reset the find cursor position to 0,0.
// Otherwise, the cursor position will be preserved so that subsequent
// searches will start from the same position. This includes appending
// characters to the search string or Ctrl-A+delete clearing of the
// search string.

export default defineComponent({
  props: {
    harmonizerApi: {
      type: Object as PropType<HarmonizerApi>,
      required: true,
    },
  },
  setup({ harmonizerApi }) {
    // search matches, sorted by (col, row)
    const results: Ref<SearchResult[]> = ref([]);
    // search query
    const query: Ref<string | null> = ref('');
    // replacement term
    const replacement: Ref<string> = ref('');
    // points to next result
    const cursor: Ref<number> = ref(0);
    // last result at cursor
    const result: Ref<SearchResult> = ref({ row: 0, col: 0 });
    // number of results
    const count = computed(() => results.value.length);

    // cyclically scroll the cursor
    function scroll(offset: number) {
      const n = count.value || 1;
      const i = cursor.value + offset;
      cursor.value = ((i % n) + n) % n;
      // clear highlighting
      harmonizerApi.highlight();
      if (query.value === null) {
        // reset to result origin if the query has been cleared
        result.value = { row: 0, col: 0 };
      } else if (count.value > 0) {
        // update result if there's a valid query
        result.value = results.value[cursor.value];
        // highlight the result
        harmonizerApi.highlight(result.value.row, result.value.col);
        harmonizerApi.scrollViewportTo(result.value.row, result.value.col);
      }
    }
    const next = () => scroll(1);
    const previous = () => scroll(-1);

    // update results with the current query and the current handsontable data
    function updateResults() {
      // comparator for sorting search results
      function comparator(a: SearchResult, b: SearchResult) {
        return a.col - b.col || a.row - b.row;
      }
      // update results
      results.value = harmonizerApi
        .find(query.value || '')
        .sort(comparator);
      // find leftmost insertion point
      let low = 0;
      let high = count.value - 1;
      while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        if (comparator(results.value[mid], result.value) >= 0) {
          high = mid - 1;
        } else {
          low = mid + 1;
        }
      }
      // seek cursor to leftmost insertion point
      scroll(low - cursor.value);
    }

    // replace the text at the current cursor position or all results with the replacement term
    function replace(all:boolean) {
      // array of SearchResults to perform replacements on
      const resultsToChange = all ? results.value : [result.value];
      // array of CellDatas with the replacement applied
      const replacements = resultsToChange.map((r) => {
        const data = harmonizerApi.getCellData(r.row, r.col);
        data.text = data.text.replace(query.value || '', replacement.value || '');
        return data;
      });
      // replace the text in Handsontable
      harmonizerApi.setCellData(replacements);
      // update the results to respect the new text
      updateResults();
    }
    const replaceOnce = () => replace(false);
    const replaceAll = () => replace(true);

    // update the search results when the query changes
    watch(query, () => updateResults());

    return {
      next,
      previous,
      replacement,
      scroll,
      query,
      count,
      result,
      results,
      cursor,
      replace,
      replaceOnce,
      replaceAll,
    };
  },
});
</script>

<template>
  <div>
    <div class="d-flex align-center">
      <v-form
        style="width: 100%"
        @submit.prevent="next"
      >
        <v-text-field
          v-model="query"
          clearable
          label="Find"
          :counter="query ? count : undefined"
          :counter-value="query ? () => (count ? cursor + 1 : 0) : null"
        />
      </v-form>
      <v-tooltip left>
        <template #activator="{ on, attrs }">
          <v-btn
            icon
            v-bind="attrs"
            v-on="on"
            @click="previous"
          >
            <v-icon>mdi-arrow-up-thin</v-icon>
          </v-btn>
        </template>
        <span>Find previous</span>
      </v-tooltip>
      <v-tooltip left>
      <template #activator="{ on, attrs }">
        <v-btn
          icon
          v-bind="attrs"
          v-on="on"
          @click="next"
        >
          <v-icon>mdi-arrow-down-thin</v-icon>
        </v-btn>
      </template>
      <span>Find next</span>
    </v-tooltip>
    </div>

    <div class="d-flex align-center">
      <v-text-field
        v-model="replacement"
        clearable
        label="Replace"
      />
      <v-tooltip left>
        <template #activator="{ on, attrs }">
          <v-btn
            icon
            v-bind="attrs"
            v-on="on"
            @click="replaceOnce"
          >
            <v-icon>mdi-repeat-once</v-icon>
          </v-btn>
        </template>
        <span>Replace</span>
      </v-tooltip>
      <v-tooltip left>
      <template #activator="{ on, attrs }">
        <v-btn
          icon
          v-bind="attrs"
          v-on="on"
          @click="replaceAll"
        >
          <v-icon>mdi-repeat</v-icon>
        </v-btn>
      </template>
      <span>Replace all</span>
    </v-tooltip>
    </div>
  </div>
</template>

<style lang="scss">
</style>
