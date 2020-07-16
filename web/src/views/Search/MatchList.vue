<script>
import { mapGetters, mapActions, mapState } from 'vuex';
import { valueDisplayName } from '@/util';

export default {
  props: {
    field: {
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
    ...mapGetters(['type', 'conditions']),
    otherConditions() {
      return this.conditions.filter((c) => (c.field !== this.field));
    },
    myConditions() {
      return this.conditions.filter((c) => (c.field === this.field));
    },
  },

  watch: {
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
      await this.fetchFacetSummary({ field: this.field, conditions: this.otherConditions });
      const items = this.facetSummaries[this.type][this.field];
      if (items.length) {
        this.selected = this.myConditions.map((c) => ({
          count: items.find((item) => item.facet.toLowerCase() === c.value.toLowerCase()).count,
          facet: c.value,
        }));
        this.items = items.map((item) => ({
          ...item,
          name: valueDisplayName(this.field, item.facet),
        }));
      } else {
        this.selected = [];
        this.items = [];
      }
    },
    setSelected({ item, value }) {
      let conditions;
      if (value) {
        conditions = [...this.conditions, {
          op: '==',
          field: this.field,
          value: item.facet,
        }];
      } else {
        conditions = this.conditions
          .filter((c) => !(c.field === this.field && c.value === item.facet));
      }
      this.$router.push({ query: { conditions } });
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
