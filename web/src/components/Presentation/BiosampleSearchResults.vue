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
import { snakeToSentenceCase } from '@/data/utils';

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
      <div class="d-flex ga-1 align-center">
        <span class="flex-shrink-0 text-no-wrap">
          <strong class="mr-1">ID:</strong>
          <ClickToCopyText background-color="#ffffff">
            {{ result.id }}
          </ClickToCopyText>
        </span>
        <v-icon>mdi-circle-small</v-icon>
        <span class="flex-shrink-0 text-no-wrap">
          <strong class="mr-2">Study ID:</strong>
          <ClickToCopyText background-color="#ffffff">
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
                <ClickToCopyText
                  background-color="#ffffff"
                  icon-overlay
                >
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
          class="justify-end"
          :to="{ name: 'Sample', params: { id: result.id } }"
        >
          <v-tooltip
            v-if="(result as BiosampleSearchResult).badges.length > 0"
            max-width="340px"
          >
            <template #activator="{ props }">
              <div
                class="d-flex align-center mr-2"
                v-bind="props"
              >
                <v-icon size="small">
                  mdi-medal
                </v-icon>
                <div class="text-body-2">{{ (result as BiosampleSearchResult).badges.length }}</div>
              </div>
            </template>
            <span class="d-flex flex-wrap">
              <span>This biosample has {{ (result as BiosampleSearchResult).badges.length }} metadata quality badges:</span>
              <span class="d-inline-flex ga-1 mt-2 mb-1 flex-wrap">
                <v-chip
                  v-for="badge in (result as BiosampleSearchResult).badges"
                  :key="badge"
                  size="small"
                >
                  {{ snakeToSentenceCase(badge) }}
                </v-chip>
              </span>
              <!-- <ul>
                <li
                  v-for="badge in (result as BiosampleSearchResult).badges"
                  :key="badge"
                >
                  {{ snakeToSentenceCase(badge) }}
                </li>
              </ul> -->
            </span>
          </v-tooltip>
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
