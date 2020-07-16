<script>
import { mapGetters, mapActions } from 'vuex';
import { types } from '@/encoding';
import FacetedSearch from '@/components/Presentation/FacetedSearch.vue';

export default {
  components: { FacetedSearch },
  data: () => ({
    types,
    tableHeaders: [
      {
        text: 'Facet', value: 'facet', sortable: true,
      },
      {
        text: 'Count', value: 'count', sortable: true, width: 90,
      },
    ],

  }),
  computed: {
    ...mapGetters(['type', 'conditions', 'primitiveFields', 'facetSummary']),
    typeFields() {
      return this.primitiveFields(this.type);
    },
  },
  methods: mapActions(['fetchFacetSummary']),
};
</script>

<template>
  <v-navigation-drawer
    app
    clipped
    permanent
  >
    <div class="ma-3">
      <div class="text-subtitle-2 primary--text">
        I am looking for...
      </div>
      <v-btn-toggle
        :value="type"
        mandatory
        dense
        class="my-3"
      >
        <template v-for="t in Object.keys(types)">
          <v-btn
            v-if="types[t].visible || type === t"
            :key="t"
            :value="t"
            :text="type !== t"
            :color="type === t ? 'primary' : 'inherit'"
            :class="{ 'white--text': type === t }"
            x-small
            @click="$router.push({ name: 'Search', params: { type: t } })"
          >
            {{ types[t].heading }}
          </v-btn>
        </template>
      </v-btn-toggle>
      <div class="text-subtitle-2 primary--text">
        That match the following
      </div>
    </div>
    <v-divider class="my-3" />
    <FacetedSearch
      :conditions="conditions"
      :type="type"
      :fields="typeFields"
    >
      <template #menu="{ field, isOpen }">
        <v-data-table
          v-if="isOpen && fetchFacetSummary(field) && facetSummary(type)[field]"
          dense
          :items="facetSummary(type)[field]"
          :headers="tableHeaders"
        />
      </template>
    </FacetedSearch>
  </v-navigation-drawer>
</template>
