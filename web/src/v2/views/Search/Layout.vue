<script lang="ts">
import { defineComponent } from '@vue/composition-api';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
import { api } from '@/data/api';

import { conditions } from '@/v2/store';
import usePaginatedResults from '@/v2/use/usePaginatedResults';

import BiosampleVisGroup from './BiosampleVisGroup.vue';
import Sidebar from './Sidebar.vue';

export default defineComponent({
  name: 'LayoutV2',

  components: {
    BiosampleVisGroup,
    SearchResults,
    Sidebar,
  },

  setup() {
    const biosampleType = types.biosample;
    const biosample = usePaginatedResults(conditions, api.searchBiosample);

    const studyType = types.study;
    const study = usePaginatedResults(conditions, api.searchStudy, 3);

    function nagivateToSelected(args: unknown) {
      console.log(args);
    }

    return {
      biosampleType,
      biosample,
      nagivateToSelected,
      studyType,
      study,
    };
  },
});
</script>

<template>
  <div>
    <sidebar :results-count="biosample.data.results.count" />
    <v-main>
      <v-container fluid>
        <v-row>
          <v-col>
            <BiosampleVisGroup />
            <SearchResults
              :count="study.data.results.count"
              :icon="studyType.icon"
              :items-per-page="study.data.limit"
              :results="study.data.results.results"
              :page="study.page.value"
              @set-page="study.setPage($event)"
              @selected="navigateToSelected($event)"
            />
            <SearchResults
              :count="biosample.data.results.count"
              :icon="biosampleType.icon"
              :items-per-page="biosample.data.limit"
              :results="biosample.data.results.results"
              :page="biosample.page.value"
              @set-page="biosample.setPage($event)"
              @selected="navigateToSelected($event)"
            />
            <h2 v-if="biosample.data.results.results === 0">
              No results for selected conditions in {{ type }}
            </h2>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </div>
</template>
