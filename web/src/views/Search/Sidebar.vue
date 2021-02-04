<script>
import Vue from 'vue';
import { mapGetters, mapState } from 'vuex';
import { types } from '@/encoding';
import { api } from '@/data/api';
import FacetedSearch from '@/components/Presentation/FacetedSearch.vue';
import ConditionChips from '@/components/Presentation/ConditionChips.vue';
import MenuContent from '@/components/Presentation/MenuContent.vue';

export default Vue.extend({
  components: {
    ConditionChips,
    FacetedSearch,
    MenuContent,
  },

  data: () => ({
    types,
  }),

  asyncComputed: {
    dbSummary: {
      async get() { return api.getDatabaseSummary(); },
      default: {},
    },
  },

  computed: {
    ...mapState(['results']),
    ...mapGetters(['type', 'conditions']),
    typeSummary() {
      if (this.type in this.dbSummary) {
        return this.dbSummary[this.type].attributes;
      }
      return {};
    },
    primitiveFields() {
      return Object.keys(this.typeSummary);
    },
    typeResultsCount() {
      const tr = this.results[this.type];
      return tr ? tr.count : 0;
    },
  },

  methods: {
    removeCondition({ field, value, table }) {
      this.$store.dispatch('route', {
        conditions: this.conditions
          .filter((c) => !(
            c.field === field
            && (value ? c.value === value : true)
            && c.table === table
          )),
      });
    },
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
      <div class="text-subtitle-2 primary--text">
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
      </v-chip-group>
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
      @remove="removeCondition"
    >
      <template #menu="{ field, table, isOpen }">
        <MenuContent
          v-bind="{
            field,
            table,
            isOpen,
            conditions,
            summary: (dbSummary[table] || {})[field],
          }"
          @select="$store.dispatch('route', $event)"
        />
      </template>
    </ConditionChips>

    <div class="font-weight-bold text-subtitle-2 primary--text mx-3">
      Found {{ typeResultsCount }} results.
    </div>

    <v-divider class="my-3" />

    <FacetedSearch
      :conditions="conditions"
      :type="type"
      :fields="primitiveFields"
    >
      <template #menu="{ field, isOpen }">
        <MenuContent
          v-bind="{
            field,
            table: type,
            isOpen,
            conditions,
            summary: typeSummary[field],
          }"
          @select="$store.dispatch('route', $event)"
        />
      </template>
    </FacetedSearch>
  </v-navigation-drawer>
</template>
