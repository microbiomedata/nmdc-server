<script lang="ts">
import {
  computed, defineComponent, ref, watch,
} from 'vue';
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';

import { geneFunctionTables, types } from '@/encoding';
import {
  api, AttributeSummary, Condition, DatabaseSummaryResponse, entityType,
} from '@/data/api';

import ConditionChips from '@/components/Presentation/ConditionChips.vue';

import MenuContent from '@/components/MenuContent.vue';
import FacetedSearch, { SearchFacet } from '@/components/FacetedSearch.vue';

import {
  stateRefs, removeConditions, setConditions, toggleConditions,
} from '@/store';
import useGtag from '@/use/useGtag';

/**
 * Sidebar has a fixed list of facets, possibly from different tables.
 */
const FunctionSearchFacets: SearchFacet[] = [
  {
    field: 'id',
    table: 'kegg_function',
  },
  {
    field: 'id',
    table: 'cog_function',
  },
  {
    field: 'id',
    table: 'pfam_function',
  },
  {
    field: 'id',
    table: 'go_function',
  },
  /** MIxS Environmental Triad */
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
  /** Data Generation */
  {
    field: 'instrument_name',
    table: 'omics_processing',
    group: 'Data Generation',
  },
  {
    field: 'omics_type',
    table: 'omics_processing',
    group: 'Data Generation',
  },
  {
    field: 'processing_institution',
    table: 'omics_processing',
    group: 'Data Generation',
  },
  {
    field: 'mass_spectrometry_configuration_name',
    table: 'omics_processing',
    group: 'Data Generation',
  },
  {
    field: 'chromatography_configuration_name',
    table: 'omics_processing',
    group: 'Data Generation',
  },
  {
    field: 'metaproteomics_analysis_category',
    table: 'metaproteomic_analysis',
    group: 'Workflow Execution',
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
    const gtag = useGtag();
    const biosampleDescription = computed(() => {
      const { schemaName } = types.biosample;
      if (schemaName !== undefined) {
        // @ts-ignore
        const schema = NmdcSchema.classes[schemaName];
        return schema.description || '';
      }
      return '';
    });

    api.getDatabaseSummary().then((s) => { dbSummary.value = s; });

    function dbSummaryForTable(table: entityType, field: string): AttributeSummary {
      if (table in dbSummary.value) {
        return dbSummary.value[table].attributes[field] as AttributeSummary;
      }
      if (geneFunctionTables.includes(table)) {
        const tableToType: Record<string, string> = {
          kegg_function: 'kegg_function',
          cog_function: 'cog_function',
          pfam_function: 'pfam_function',
          go_function: 'go_function',
        };
        return {
          type: tableToType[table],
        } as AttributeSummary;
      }
      return {} as AttributeSummary;
    }

    async function updateSearch() {
      if (filterText.value.length >= 2) {
        textSearchResults.value = await api.textSearch(filterText.value);
      } else {
        textSearchResults.value = [];
      }
    }
    watch(filterText, updateSearch);

    function trackFilterConditions(newConditionList: Condition[], oldConditionList: Condition[]) {
      // Do nothing if Google Analytics is not available. This is expected in development mode.
      if (!gtag) {
        return;
      }
      // On initial load, track each filter condition that exists
      // Otherwise, track the last filter condition added or updated
      if (oldConditionList.length === 0 && newConditionList.length > 0) {
        newConditionList.forEach((condition) => {
          gtag.event('filter_added', {
            event_category: 'search',
            event_label: condition.field,
            value: condition.value,
          });
        });
      } else if (newConditionList.length > oldConditionList.length || newConditionList.length === oldConditionList.length) {
        gtag.event('filter_added', {
          event_category: 'search',
          event_label: newConditionList[newConditionList.length - 1].field,
          value: newConditionList[newConditionList.length - 1].value,
        });
        // Special case for map usage: if lat/lon were the last two filters added
        // then track both filters because they are added together from the map interface
        if (newConditionList[newConditionList.length - 1].field === 'longitude' && newConditionList[newConditionList.length - 2].field === 'latitude') {
          gtag.event('filter_added', {
            event_category: 'search',
            event_label: newConditionList[newConditionList.length - 2].field,
            value: newConditionList[newConditionList.length - 2].value,
          });
        }
      }
    }

    watch(stateRefs.conditions, trackFilterConditions);

    return {
      /* data */
      biosampleDescription,
      conditions: stateRefs.conditions,
      dbSummary,
      textSearchResults,
      filterText,
      FunctionSearchFacets,
      types,
      /* methods */
      dbSummaryForTable,
      removeConditions,
      setConditions,
      toggleConditions,
    };
  },
});
</script>

<template>
  <v-navigation-drawer
    permanent
    width="320"
  >
    <template #prepend>
      <div class="mx-3 my-2">
        <div
          v-if="conditions.length"
          class="text-subtitle-2 text-primary d-flex align-center"
        >
          <span class="flex-fill">Active query terms</span>
          <v-tooltip
            location="bottom"
            open-delay="600"
          >
            <template #activator="{ props }">
              <v-btn
                variant="plain"
                size="x-small"
                v-bind="props"
                @click="removeConditions"
              >
                <v-icon class="mr-2">mdi-filter-off</v-icon>
                Clear all
              </v-btn>
            </template>
            <span>Clear query terms</span>
          </v-tooltip>
        </div>
      </div>

      <ConditionChips
        v-if="conditions.length"
        :conditions="conditions"
        :db-summary="dbSummary"
        class="ma-3"
        style="max-height: 50vh; overflow: auto;"
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

      <div class="font-weight-bold text-subtitle-2 text-primary mx-3">
        <span v-if="isLoading">
          Loading results...
        </span>
        <span v-else class="d-flex align-center">
          <span>Found {{ resultsCount }} samples.</span>
          <v-tooltip
            location="bottom"
            open-delay="600"
          >
            <template #activator="{ props }">
              <v-btn
                icon
                variant="plain"
                size="x-small"
                v-bind="props"
              >
                <v-icon>mdi-help-circle</v-icon>
              </v-btn>
            </template>
            <span>{{ biosampleDescription }}</span>
          </v-tooltip>
        </span>
      </div>

      <v-divider class="my-3" />
    </template>

    <FacetedSearch
      v-model:filter-text="filterText"
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
