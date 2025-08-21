<script lang="ts">
import {
  computed, defineComponent, ref, watch,
} from '@vue/composition-api';
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';

import { geneFunctionTables, types } from '@/encoding';
import {
  api, Condition, DatabaseSummaryResponse, entityType,
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

    function dbSummaryForTable(table: entityType, field: string) {
      if (table in dbSummary.value) {
        return dbSummary.value[table].attributes[field];
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
        };
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

    function trackFilterConditions(val: Condition[], oldVal: Condition[]) {
      // Do nothing if Google Analytics is not available. This is expected in development mode.
      if (!gtag) {
        return;
      }
      // On initial load, track each filter condition that exists
      // Otherwise, track the last filter condition added or updated
      if (oldVal.length === 0 && val.length > 0) {
        val.forEach((condition) => {
          gtag.event('filter_added', {
            event_category: 'search',
            event_label: condition.field,
            value: condition.value,
          });
        });
      } else if (val.length > oldVal.length || val.length === oldVal.length) {
        gtag.event('filter_added', {
          event_category: 'search',
          event_label: val[val.length - 1].field,
          value: val[val.length - 1].value,
        });
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
    app
    clipped
    permanent
    width="320"
  >
    <template #prepend>
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

      <div class="font-weight-bold text-subtitle-2 primary--text mx-3">
        <span v-if="isLoading">
          Loading results...
        </span>
        <span v-else>Found {{ resultsCount }} samples.
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
