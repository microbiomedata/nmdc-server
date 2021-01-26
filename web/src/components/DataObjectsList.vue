<script lang="ts">
/**
 * Component for listing the data objects associated with a
 * given entity.  Only some entity types are supported.
 */
import Vue, { PropType } from 'vue';

import { api, DataObjectSearchResult, entityType } from '@/data/api';
import SearchResults from '@/components/Presentation/SearchResults.vue';

export default Vue.extend({
  components: {
    SearchResults,
  },
  props: {
    type: {
      type: String as PropType<entityType>,
      required: true,
    },
    id: {
      type: String as PropType<string>,
      required: true,
    },
  },

  asyncComputed: {
    results: {
      async get(): Promise<DataObjectSearchResult[]> {
        return api.getDataObjectList(this.type, this.id);
      },
      default: [],
    },
  },
});
</script>

<template>
  <div v-if="results.length">
    <div class="display-1 my-4">
      Data Objects
    </div>
    <search-results
      type="data_object"
      :page="1"
      :items-per-page="results.length"
      :count="results.length"
      :results="results"
    />
  </div>
</template>
