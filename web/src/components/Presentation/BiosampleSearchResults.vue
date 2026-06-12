<script setup lang="ts">
import {
  computed,
  reactive,
} from 'vue';
import SearchResults from '@/components/Presentation/SearchResults.vue';
import SampleListExpansion from '@/components/SampleListExpansion.vue';
import { types } from '@/encoding';
import { PaginatedResult } from '@/use/usePaginatedResults';
import { BiosampleSearchResult, DataObjectFilter } from '@/data/api';
import { stateRefs } from '@/store';

const { biosampleSearch, dataObjectFilter } = defineProps<{
  biosampleSearch: PaginatedResult<BiosampleSearchResult>;
  dataObjectFilter: DataObjectFilter[];
}>();

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
</script>

<template>
  <SearchResults
    :count="biosampleSearch.data.results.count"
    :icon="biosampleType.icon"
    :items-per-page="biosampleSearch.data.limit"
    :results="biosampleSearch.data.results.results"
    :page="biosampleSearch.data.pageSync"
    :loading="biosampleSearch.loading.value"
    @set-page="biosampleSearch.setPage($event)"
    @set-items-per-page="biosampleSearch.setItemsPerPage($event)"
  >
    <template #item-title="{ result }">
      <router-link
        :to="{ name: 'Sample', params: { id: result.id }}"
      >
        <span class="text-subtitle-2">
          {{ result.name }}
        </span>
      </router-link>
    </template>
    <template #item-subtitle="{ result }">
      <div class="d-flex ga-1">
        <span class="flex-shrink-0 text-no-wrap">
          <strong class="mr-1">ID:</strong>
          <ClickToCopyText>
            {{ result.id }}
          </ClickToCopyText>
        </span>
        <v-icon>mdi-circle-small</v-icon>
        <span class="flex-shrink-0 text-no-wrap">
          <strong class="mr-2">Study ID:</strong>
          <ClickToCopyText>
            {{ (result as BiosampleSearchResult).study_id }}
          </ClickToCopyText>
        </span>
        <template
          v-if="result.alternate_identifiers.length || (result as BiosampleSearchResult).emsl_biosample_identifiers.length"
        >
          <v-icon>mdi-circle-small</v-icon>
          <strong class="mr-2">External:</strong>
          <span class="identifiers-slide-group">
            <v-slide-group
              show-arrows
              next-icon="mdi-chevron-double-right"
              prev-icon="mdi-chevron-double-left"
              class="align-center"
            >
              <v-slide-group-item
                v-for="id in result.alternate_identifiers"
                :key="id"
              >
                <a
                  :href="`https://identifiers.org/${id}`"
                  class="pr-2 text-grey-darken-2 text-decoration-underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {{ id }}
                </a>
              </v-slide-group-item>
              <v-slide-group-item
                v-for="id in result.emsl_biosample_identifiers"
                :key="id"
              >
                <ClickToCopyText icon-overlay>
                  {{ id }}
                </ClickToCopyText>
              </v-slide-group-item>
            </v-slide-group>
          </span>
        </template>
      </div>
    </template>
    <template #item-content="props">
      <SampleListExpansion
        v-bind="{
          result: props.result as BiosampleSearchResult,
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

<style lang="scss" scoped>
.identifiers-slide-group {
  max-width: 500px;
  overflow: hidden;
}
</style>
