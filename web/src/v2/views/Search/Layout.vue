<script lang="ts">
import { defineComponent, reactive } from '@vue/composition-api';

import SearchResults from '@/components/Presentation/SearchResults.vue';
import { types } from '@/encoding';
import { api } from '@/data/api';

import { conditions } from '@/v2/store';
import usePaginatedResults from '@/v2/use/usePaginatedResults';
import SampleListExpansion from '@/v2/components/SampleListExpansion.vue';

import BiosampleVisGroup from './BiosampleVisGroup.vue';
import Sidebar from './Sidebar.vue';

export default defineComponent({
  name: 'LayoutV2',

  components: {
    BiosampleVisGroup,
    SampleListExpansion,
    SearchResults,
    Sidebar,
  },

  setup() {
    const expandedOmicsDetails = reactive({
      id: null as string | null,
      type: null as string | null,
    });

    function setExpanded({ id, type }: { id: string; type: string; }) {
      expandedOmicsDetails.id = id;
      expandedOmicsDetails.type = type;
    }

    const biosampleType = types.biosample;
    const biosample = usePaginatedResults(conditions, api.searchBiosample);

    const studyType = types.study;
    const study = usePaginatedResults(conditions, api.searchStudy, 3);

    return {
      /* data */
      expandedOmicsDetails,
      biosampleType,
      biosample,
      studyType,
      study,
      /* methods */
      setExpanded,
    };
  },
});
</script>

<template>
  <div>
    <sidebar :results-count="biosample.data.results.count" />
    <v-main>
      <v-container
        fluid
        class="py-0"
      >
        <v-row>
          <v-col>
            <BiosampleVisGroup />
            <v-card outlined>
              <v-card-title class="pb-0">
                Studies
              </v-card-title>
              <SearchResults
                disable-pagination
                disable-navigate-on-click
                :count="study.data.results.count"
                :icon="studyType.icon"
                :items-per-page="study.data.limit"
                :results="study.data.results.results"
                :page="study.data.pageSync"
                @set-page="study.setPage($event)"
                @selected="$router.push({ name: 'V2Sample'})"
              >
                <template #action>
                  <v-list-item-action>
                    <v-checkbox />
                  </v-list-item-action>
                </template>
              </SearchResults>
            </v-card>
            <v-card class="my-4">
              <v-card-title class="pb-0">
                Samples
              </v-card-title>
              <SearchResults
                disable-navigate-on-click
                :count="biosample.data.results.count"
                :icon="biosampleType.icon"
                :items-per-page="biosample.data.limit"
                :results="biosample.data.results.results"
                :page="biosample.data.pageSync"
                @set-page="biosample.setPage($event)"
                @selected="$router.push({ name: 'V2Sample', params: { id: $event }})"
              >
                <template #item-content="props">
                  <SampleListExpansion
                    v-bind="{
                      result: props.result,
                      expanded: expandedOmicsDetails,
                    }"
                    @open-details="setExpanded({ id: props.result.id, type: $event })"
                  />
                </template>
              </SearchResults>
              <h2 v-if="biosample.data.results.count === 0">
                No results for selected conditions in sample table
              </h2>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </div>
</template>
