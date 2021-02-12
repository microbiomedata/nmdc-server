<script>
import Vue from 'vue';
import FacetSummary from '@/mixins/FacetSummary';

export default Vue.extend({
  mixins: [FacetSummary],

  data: () => ({
    createdDelay: false,
    filterText: '',
    tableHeaders: [
      {
        text: 'Facet',
        value: 'name',
        width: '300',
        sortable: true,
      },
      {
        text: 'Count',
        value: 'count',
        sortable: true,
        width: 90,
        filterable: false,
      },
    ],
  }),

  computed: {
    selected() {
      return this.myConditions.map(
        // In order for selection to work, each object must match for all key/value pairs
        // so we have to get the right item from the item list where value matches
        (c) => this.facetSummary.find((item) => item.facet.toLowerCase() === c.value.toLowerCase()),
      );
    },
  },

  created() {
    /* Enable loading bar after 2 seconds of no load, to avoid overly noisy facet dialogs */
    window.setTimeout(() => { this.createdDelay = true; }, 2000);
  },

  methods: {
    setSelected({ item, value }) {
      let conditions;
      if (value) {
        conditions = [...this.conditions, {
          op: '==',
          field: this.field,
          value: item.facet,
          table: this.table,
        }];
      } else {
        conditions = this.conditions
          .filter((c) => !(
            c.field === this.field
            && c.value === item.facet
            && c.table === this.table
          ));
      }
      this.$emit('select', { conditions });
    },

    toggleSelectAll({ items, value }) {
      if (value) {
        this.$emit('select', {
          conditions: [
            ...this.otherConditions,
            ...items
              .filter((item) => item.isSelectable)
              .map((item) => ({
                op: '==',
                field: this.field,
                value: item.facet,
                table: this.table,
              })),
          ],
        });
      } else {
        this.$emit('select', { conditions: this.otherConditions });
      }
    },
  },
});
</script>

<template>
  <div class="match-list-table">
    <v-text-field
      v-model="filterText"
      solo
      label="search"
      clearable
      class="px-3 my-3"
      dense
      hide-details
      outlined
      flat
      append-icon="mdi-magnify"
    />
    <v-data-table
      :value="selected"
      dense
      show-select
      height="355px"
      :items-per-page="10"
      :search="filterText"
      :item-key="'facet'"
      :items="facetSummaryAggregate"
      :headers="tableHeaders"
      :no-data-text="'Data is loading.'"
      :loading="facetSummaryAggregate.length === 0 && createdDelay"
      :loading-text="'Data is loading and could take a while.'"
      @item-selected="setSelected"
      @toggle-select-all="toggleSelectAll"
    >
      <template v-slot:item.name="{ item }">
        <span :class="{ 'grey--text': !item.isSelectable }">
          {{ item.name }}
        </span>
      </template>
    </v-data-table>
  </div>
</template>

<style lang="scss">
.match-list-table {
  .v-data-table {
    table {
      table-layout: fixed;
    }

    td {
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
  }
}
</style>
