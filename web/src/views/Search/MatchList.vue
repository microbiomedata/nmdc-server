<script>
import { mapGetters, mapActions, mapState } from 'vuex';
import { valueDisplayName } from '@/util';

export default {
  props: {
    field: {
      type: String,
      required: true,
    },
    type: {
      type: String,
      required: true,
    },
  },
  data: () => ({
    filterText: '',
    items: [],
    selected: [],
    tableHeaders: [
      {
        text: 'Facet',
        value: 'name',
        sortable: true,
      },
      {
        text: 'Count',
        value: 'count',
        sortable: true,
        width: 90,
      },
    ],
  }),

  computed: {
    ...mapState(['facetSummaries']),
    ...mapGetters(['conditions']),

    otherConditions() {
      // conditions from OTHER fields
      return this.conditions.filter((c) => (c.field !== this.field) || (c.table !== this.type));
    },
    myConditions() {
      // conditions that match our field.
      return this.conditions.filter((c) => (c.field === this.field) && (c.table === this.type));
    },
  },

  watch: {
    // Vuex will invalidate this cache when necessary,
    // so we can listen to the object to know when to reload.
    facetSummaries: {
      handler: 'updateSelected',
      deep: true,
    },
  },

  created() {
    this.updateSelected();
  },

  methods: {
    ...mapActions(['fetchFacetSummary']),

    async updateSelected() {
      // get the summary for our facet, NOT including the conditions already selected
      // that pertain to our facet.  This is done so that all facet options for the current facet
      // will be visible (and selectable).  Counts will be wrong.
      await this.fetchFacetSummary({
        field: this.field,
        conditions: this.otherConditions,
        type: this.type,
      });
      // Results from the above action are cached in facetSummaries.
      const allFacets = this.facetSummaries[this.type][this.field];
      // if there were results, figure out which ones should be selected based on
      // the active list of conditions.
      this.selected = this.myConditions.map(
        // In order for selection to work, each object must match for all key/value pairs
        // so we have to get the right item from the item list where value matches
        (c) => allFacets.find((item) => item.facet.toLowerCase() === c.value.toLowerCase()),
      );
      this.items = allFacets.map((item) => ({
        ...item,
        name: valueDisplayName(this.field, item.facet),
      }));
    },

    setSelected({ item, value }) {
      let conditions;
      if (value) {
        conditions = [...this.conditions, {
          op: '==',
          field: this.field,
          value: item.facet,
          table: this.type,
        }];
      } else {
        conditions = this.conditions
          .filter((c) => !(
            c.field === this.field
            && c.value === item.facet
            && c.table === this.type
          ));
      }
      this.$store.dispatch('route', { conditions });
    },
  },
};
</script>

<template>
  <div>
    <v-text-field
      :value="filterText"
      solo
      label="search"
      clearable
      class="px-3 my-3"
      dense
      hide-details
      outlined
      flat
      append-icon="mdi-magnify"
      @input="$set(filterText, field, $event)"
    />
    <v-data-table
      :value="selected"
      dense
      show-select
      :items-per-page="20"
      :search="filterText"
      :item-key="'facet'"
      :items="items"
      :headers="tableHeaders"
      @item-selected="setSelected"
    />
  </div>
</template>
