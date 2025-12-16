<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  reactive,
} from 'vue';
import SearchResults from '@/components/Presentation/SearchResults.vue';
import SampleListExpansion from '@/components/SampleListExpansion.vue';
import { types } from '@/encoding';
import { PaginatedResult } from '@/use/usePaginatedResults';
import { BiosampleSearchResult, DataObjectFilter } from '@/data/api';
import { stateRefs } from '@/store';

export default defineComponent({
  components: { SampleListExpansion, SearchResults },
  props: {
    biosampleSearch: {
      type: Object as PropType<PaginatedResult<BiosampleSearchResult>>,
      required: true,
    },
    dataObjectFilter: {
      type: Array as PropType<DataObjectFilter[]>,
      required: true,
    },
  },
  setup() {
    const biosampleType = types.biosample;

    const loggedInUser = computed(() => stateRefs.user.value !== null);

    /**
     * Expanded Omics details
     */
    const expandedOmicsDetails = reactive({
      resultId: '',
      omicsProcessingId: '',
    });
    function setExpanded(resultId: string, omicsProcessingId: string) {
      if (expandedOmicsDetails.resultId !== resultId
        || expandedOmicsDetails.omicsProcessingId !== omicsProcessingId) {
        expandedOmicsDetails.resultId = resultId;
        expandedOmicsDetails.omicsProcessingId = omicsProcessingId;
      } else {
        expandedOmicsDetails.resultId = '';
        expandedOmicsDetails.omicsProcessingId = '';
      }
    }

    return {
      biosampleType,
      expandedOmicsDetails,
      setExpanded,
      loggedInUser,
    };
  },
});
</script>

<template>
  <SearchResults
    disable-navigate-on-click
    :count="biosampleSearch.data.results.count"
    :icon="biosampleType.icon"
    :items-per-page="biosampleSearch.data.limit"
    :results="biosampleSearch.data.results.results"
    :page="biosampleSearch.data.pageSync"
    :subtitle-key="'study_id'"
    :loading="biosampleSearch.loading.value"
    @set-page="biosampleSearch.setPage($event)"
    @selected="$router.push({ name: 'Sample', params: { id: $event }})"
    @set-items-per-page="biosampleSearch.setItemsPerPage($event)"
  >
    <template #subtitle="props">
      <span class="pr-2">Study ID:</span>
      <router-link
        :to="{name: 'Study', params: { id: props.result.study_id }}"
        class="pr-2 text-grey-darken-2"
        v-text="props.result.study_id"
      />
      <template
        v-if="props.result.alternate_identifiers.length || props.result.emsl_biosample_identifiers.length"
      >
        <span class="pr-2">Sample Identifiers:</span>
        <a
          v-for="id in props.result.alternate_identifiers"
          :key="id"
          :href="`https://identifiers.org/${id}`"
          class="pr-2 text-grey-darken-2"
          target="_blank"
          rel="noopener noreferrer"
        >{{ id }}</a>
        <span
          v-for="id in props.result.emsl_biosample_identifiers"
          :key="id"
        >
          {{ id }}
        </span>
      </template>
    </template>
    <template #item-content="props">
      <SampleListExpansion
        v-bind="{
          result: props.result,
          expanded: expandedOmicsDetails,
          loggedInUser,
          showBulk: dataObjectFilter.length > 0,
        }"
        @open-details="setExpanded(props.result.id, $event)"
      />
    </template>
    <template #action-right="{ result }">
      <v-list-item-action>
        <v-btn
          icon
          variant="plain"
          size="large"
          :to="{ name: 'Sample', params: { id: result.id } }"
        >
          <v-icon>
            mdi-chevron-right
          </v-icon>
        </v-btn>
      </v-list-item-action>
    </template>
  </SearchResults>
</template>
