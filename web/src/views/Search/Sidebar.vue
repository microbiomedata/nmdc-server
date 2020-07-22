<script>
import { mapGetters, mapState } from 'vuex';
import { types } from '@/encoding';

import ConditionChips from '@/components/Presentation/ConditionChips.vue';
import FacetedSearch from '@/components/Presentation/FacetedSearch.vue';

import MenuContent from './MenuContent.vue';

export default {
  components: {
    ConditionChips,
    FacetedSearch,
    MenuContent,
  },

  data: () => ({
    types,
  }),

  computed: {
    ...mapState(['results']),
    ...mapGetters(['type', 'typeSummary', 'conditions', 'primitiveFields']),
    typeFields() {
      return this.primitiveFields(this.type);
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
};
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
        I am looking for...
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
        class="text-subtitle-2 primary--text"
      >
        That match the following conditions
      </div>
    </div>

    <ConditionChips
      :conditions="conditions"
      class="ma-3"
      @remove="removeCondition"
    >
      <template #menu="{ field, table, isOpen }">
        <MenuContent
          v-bind="{
            field,
            type: table,
            isOpen,
            conditions,
            summary: typeSummary(table)[field],
          }"
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
      :fields="typeFields"
    >
      <template #menu="{ field, isOpen }">
        <MenuContent
          v-bind="{
            field,
            type,
            isOpen,
            summary: typeSummary(type)[field],
            conditions,
          }"
        />
      </template>
    </FacetedSearch>
  </v-navigation-drawer>
</template>
