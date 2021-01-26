<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { types } from '@/encoding';
import { api, DatabaseSummaryResponse, entityType } from '@/data/api';

import ConditionChips from '@/components/Presentation/ConditionChips.vue';
import MenuContent from '@/components/Presentation/MenuContent.vue';

import FacetedSearch, { SearchFacet } from '@/v2/components/FacetedSearch.vue';

import { conditions, removeConditions } from '@/v2/store';

/**
 * V2's sidebar has a fixed list of facets, possibly from different tables.
 */
const FunctionSearchFacets: SearchFacet[] = [
  {
    field: 'habitat',
    table: 'biosample',
  },
  {
    field: 'depth',
    table: 'biosample',
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
  },

  setup() {
    const dbSummary = ref({} as DatabaseSummaryResponse);
    api.getDatabaseSummary().then((s) => { dbSummary.value = s; });

    function dbSummaryForTable(table: entityType, field: string) {
      if (table in dbSummary.value) {
        return dbSummary.value[table].attributes[field];
      }
      return {};
    }
    return {
      FunctionSearchFacets,
      conditions,
      dbSummary,
      dbSummaryForTable,
      removeConditions,
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
      <!-- <div class="text-subtitle-2 primary--text">
        I want to search by...
      </div>
      <v-chip-group
        :value="type"
        mandatory
        column
        class="my-1"
      >
        <template v-for="t in Object.keys(types)">
          <v-chip
            v-if="types[t].visible || type === t"
            :key="t"
            :value="t"
            :color="type === t ? 'primary' : 'inherit'"
            small
            @click="$store.dispatch('route', { name: 'Search', type: t, conditions })"
          >
            {{ types[t].heading }}
          </v-chip>
        </template>
      </v-chip-group> -->
      <div
        v-if="conditions.length"
        class="text-subtitle-2 primary--text d-flex flex-row"
      >
        <span class="grow">That match the following conditions</span>
        <v-btn
          icon
          x-small
          @click="$store.dispatch('route', { conditions: [] })"
        >
          <v-icon>mdi-filter-off</v-icon>
        </v-btn>
      </div>
    </div>

    <ConditionChips
      :conditions="conditions"
      :db-summary="dbSummary"
      class="ma-3"
      @remove="removeConditions([$event])"
    >
      <template #menu="{ field, table, isOpen }">
        <MenuContent
          v-bind="{
            field,
            type: table,
            isOpen,
            conditions,
            summary: dbSummaryForTable(table, field),
          }"
        />
      </template>
    </ConditionChips>

    <div class="font-weight-bold text-subtitle-2 primary--text mx-3">
      Found {{ resultsCount }} results.
    </div>

    <v-divider class="my-3" />

    <FacetedSearch
      :conditions="conditions"
      :fields="FunctionSearchFacets"
    >
      <template #menu="{ field, table, isOpen }">
        <MenuContent
          v-bind="{
            field,
            type: table,
            isOpen,
            summary: dbSummaryForTable(table, field),
            conditions,
          }"
        />
      </template>
    </FacetedSearch>
  </v-navigation-drawer>
</template>
