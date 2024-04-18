<script lang="ts">
import { defineComponent, ref, watch } from '@vue/composition-api';
import { types } from '@/encoding';
import {
  api, Condition, DatabaseSummaryResponse, entityType,
} from '@/data/api';

import ConditionChips from '@/components/Presentation/ConditionChips.vue';

import MenuContent from '@/components/MenuContent.vue';
import FacetedSearch, { SearchFacet } from '@/components/FacetedSearch.vue';

import {
  stateRefs, removeConditions, setConditions, toggleConditions,
} from '@/store';

/**
 * Sidebar has a fixed list of facets, possibly from different tables.
 */
const FunctionSearchFacets: SearchFacet[] = [
  {
    field: 'id',
    table: 'gene_function',
  },
  /** ENVO */
  {
    field: 'env_broad_scale',
    table: 'biosample',
  },
  {
    field: 'env_local_scale',
    table: 'biosample',
  },
  {
    field: 'env_medium',
    table: 'biosample',
  },
  /** GOLD */
  {
    field: 'gold_classification',
    table: 'biosample',
  },
  /** Biosample */
  {
    field: 'geo_loc_name',
    table: 'biosample',
    group: 'Sample',
  },
  {
    field: 'depth',
    table: 'biosample',
    group: 'Sample',
  },
  {
    field: 'latitude',
    table: 'biosample',
    group: 'Sample',
  },
  {
    field: 'longitude',
    table: 'biosample',
    group: 'Sample',
  },
  {
    field: 'collection_date',
    table: 'biosample',
    group: 'Sample',
  },
  /** Study */
  {
    field: 'principal_investigator_name',
    table: 'study',
    group: 'Study',
  },
  /** Omics Processing */
  {
    field: 'instrument_name',
    table: 'omics_processing',
    group: 'Omics Processing',
  },
  {
    field: 'omics_type',
    table: 'omics_processing',
    group: 'Omics Processing',
  },
  {
    field: 'processing_institution',
    table: 'omics_processing',
    group: 'Omics Processing',
  },
];

export default defineComponent({
  components: {
    ConditionChips,
    FacetedSearch,
    MenuContent,
  },

  props: {
    resultsCount: {
      type: Number,
      default: 0,
    },
    isLoading: {
      type: Boolean,
      default: false,
    },
  },

  setup() {
    const filterText = ref('');
    const textSearchResults = ref([] as Condition[]);
    const dbSummary = ref({} as DatabaseSummaryResponse);
    api.getDatabaseSummary().then((s) => { dbSummary.value = s; });

    function dbSummaryForTable(table: entityType, field: string) {
      if (table in dbSummary.value) {
        return dbSummary.value[table].attributes[field];
      }
      return {};
    }

    async function updateSearch() {
      if (filterText.value.length >= 2) {
        textSearchResults.value = await api.textSearch(filterText.value);
      } else {
        textSearchResults.value = [];
      }
    }
    watch(filterText, updateSearch);

    return {
      filterText,
      textSearchResults,
      setConditions,
      FunctionSearchFacets,
      conditions: stateRefs.conditions,
      dbSummary,
      dbSummaryForTable,
      removeConditions,
      toggleConditions,
      types,
    };
  },
});
</script>

<template>
  <v-navigation-drawer
    app
    clipped
    permanent
    width="320"
  >
    <div class="mx-3 my-2">
      <div
        v-if="conditions.length"
        class="text-subtitle-2 primary--text d-flex flex-row"
      >
        <span class="grow">Active query terms</span>
        <v-tooltip
          bottom
          open-delay="600"
        >
          <template #activator="{ on, attrs }">
            <v-btn
              icon
              x-small
              v-bind="attrs"
              v-on="on"
              @click="removeConditions"
            >
              <v-icon>mdi-filter-off</v-icon>
            </v-btn>
          </template>
          <span>Clear query terms</span>
        </v-tooltip>
      </div>
    </div>

    <ConditionChips
      :conditions="conditions"
      :db-summary="dbSummary"
      class="ma-3"
      @remove="removeConditions([$event])"
    >
      <template #menu="{ field, table, isOpen, toggleMenu }">
        <MenuContent
          v-bind="{
            field,
            table,
            isOpen,
            conditions,
            summary: dbSummaryForTable(table, field),
          }"
          update
          @select="setConditions($event.conditions)"
          @close="toggleMenu(false)"
        />
      </template>
    </ConditionChips>

    <div class="font-weight-bold text-subtitle-2 primary--text mx-3">
      <span v-if="isLoading">
        Loading results...
      </span>
      <span v-else>Found {{ resultsCount }} results.</span>
    </div>

    <v-divider class="my-3" />

    <FacetedSearch
      :filter-text.sync="filterText"
      :facet-values="textSearchResults"
      :conditions="conditions"
      :fields="FunctionSearchFacets"
      @select="toggleConditions([$event])"
    >
      <template #menu="{ field, table, isOpen, toggleMenu }">
        <MenuContent
          v-bind="{
            field,
            table,
            isOpen,
            summary: dbSummaryForTable(table, field),
            conditions,
          }"
          @select="setConditions($event.conditions)"
          @close="toggleMenu(false)"
        />
      </template>
    </FacetedSearch>
  </v-navigation-drawer>
</template>
