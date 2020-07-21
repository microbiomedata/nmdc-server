<script>
import { mapGetters } from 'vuex';
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
    ...mapGetters(['type', 'typeSummary', 'conditions', 'primitiveFields']),
    typeFields() {
      return this.primitiveFields(this.type);
    },
    summaryMap() {
      return this.typeSummary(this.type);
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
      <div class="text-subtitle-2 primary--text">
        That match the following
      </div>
    </div>

    <ConditionChips
      :conditions="conditions"
      :summary-map="summaryMap"
      class="ma-3"
      @remove="removeCondition"
    >
      <template #menu="{ field, table, isOpen, summary }">
        <MenuContent
          v-bind="{
            field,
            type: table,
            isOpen,
            summary,
            conditions,
          }"
        />
      </template>
    </ConditionChips>

    <v-divider class="my-3" />

    <FacetedSearch
      :conditions="conditions"
      :summary-map="summaryMap"
      :type="type"
      :fields="typeFields"
    >
      <template #menu="{ field, isOpen, summary }">
        <MenuContent
          v-bind="{
            field,
            type,
            isOpen,
            summary,
            conditions,
          }"
        />
      </template>
    </FacetedSearch>
  </v-navigation-drawer>
</template>
