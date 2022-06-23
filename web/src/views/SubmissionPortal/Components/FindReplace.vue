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

export default defineComponent({
  props: {
    harmonizerApi: {
      type: Object as PropType<HarmonizerApi>,
      required: true,
    },
  },
  setup({ harmonizerApi }) {
    // whether the find/replace dialog is visible
    const isReplaceVisible: Ref<boolean> = ref(false);
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

    watch(query, () => {
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
    });

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
      isReplaceVisible,
    };
  },
});
</script>

<template>
  <v-toolbar
    flat
    outlined
    rounded
  >
    <v-btn
      icon
      @click="isReplaceVisible = !isReplaceVisible"
    >
      <v-icon
        class="toggleUpDown"
        :class="{ rotate: isReplaceVisible }"
      >
        mdi-menu-right
      </v-icon>
    </v-btn>
    <v-form
      style="width: 100%"
      @submit.prevent="next"
    >
      <v-text-field
        v-model="query"
        :prepend-icon="isReplaceVisible ? 'mdi-find-replace' : 'mdi-text-search'"
        clearable
        label="Find"
        :counter="query ? count : undefined"
        :counter-value="query ? () => (count ? cursor + 1 : 0) : null"
        dense
        style="padding-top: 10px"
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
    <template
      v-if="isReplaceVisible"
      #extension
    >
      <v-text-field
        v-model="replacement"
        hide-details
        class="replacement"
        clearable
        label="Replace"
        dense
      />
      <v-tooltip left>
        <template #activator="{ on, attrs }">
          <v-btn
            icon
            v-bind="attrs"
            v-on="on"
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
          >
            <v-icon>mdi-repeat</v-icon>
          </v-btn>
        </template>
        <span>Replace all</span>
      </v-tooltip>
    </template>
  </v-toolbar>
</template>

<style lang="scss">
.toggleUpDown {
  transition: transform 0.1s ease-in-out !important;
}
.toggleUpDown.rotate {
  transform: rotate(90deg);
}
.replacement {
  margin-left: 70px;
}
</style>
