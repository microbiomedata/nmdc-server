<script lang="ts">
import { mapGetters } from 'vuex';

import { api } from '@/data/api';
import SearchResults from '@/components/Presentation/SearchResults.vue';

export default {
  components: {
    SearchResults,
  },
  computed: {
    ...mapGetters(['type', 'id']),
  },
  asyncComputed: {
    results: {
      async get() {
        return api.getDataObjectList(this.type, this.id);
      },
      default: [],
    },
  },
};
</script>

<template>
  <search-results
    type="data_object"
    :results="results"
  />
</template>
