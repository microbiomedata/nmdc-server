<script lang="ts">
import Vue, { PropType } from 'vue';

import { api, DataObjectSearchResult } from '@/data/api';
import SearchResults from '@/components/Presentation/SearchResults.vue';

export default Vue.extend({
  components: {
    SearchResults,
  },
  props: {
    type: {
      type: String as PropType<string>,
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
  <div>
    <div class="display-1 my-4">
      Data Objects
    </div>
    <search-results
      type="data_object"
      :results="results"
    />
  </div>
</template>
