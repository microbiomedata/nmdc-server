<script>
import { flattenDeep, uniqWith } from 'lodash';
import { api } from '@/data/api';
import { makeTree } from '@/util';

export default {
  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String,
      required: true,
    },
    conditions: {
      type: Array,
      required: true,
    },
    heirarchy: {
      type: Array,
      default: () => [
        'ecosystem',
        'ecosystem_category',
        'ecosystem_type',
        'ecosystem_subtype',
        'specific_ecosystem',
      ],
    },
  },

  data: () => ({
    filterText: '',
  }),

  asyncComputed: {
    data: {
      async get() { return api.getEnvironmentSankeyAggregation([]); },
      default: [],
    },
  },

  computed: {
    treeData() {
      return makeTree(this.data, this.heirarchy);
    },
    tree() {
      // freeze is used because tree nodes contain back-references to their parent,
      // so recursive reactivity setup would cause a max depth exception
      return Object.freeze(this.treeData.root.children);
    },
    otherConditions() {
      return this.conditions
        .filter((c) => (!this.heirarchy.includes(c.field)) || (c.table !== this.table));
    },
  },

  methods: {
    setSelected(nodeKeys) {
      const fieldChains = nodeKeys.map((k) => k.split('.'));
      const conditions = [
        ...this.otherConditions,
        ...uniqWith(flattenDeep(fieldChains.map((chain) => chain.map((field, depth) => ({
          op: '==',
          field: this.heirarchy[depth],
          value: field,
          table: this.table,
        })))), (a, b) => a.field === b.field && a.value === b.value),
      ];
      this.$store.dispatch('route', { conditions });
    },
  },
};
</script>

<template>
  <div class="tree-overflow">
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
    <v-treeview
      :items="tree"
      :search="filterText"
      selectable
      selected-color="primary"
      open-on-click
      dense
      @input="setSelected"
    />
  </div>
</template>

<style lang="scss" scoped>
.tree-overflow {
  max-height: 475px;
  height: 475px;
  overflow-y: auto;
}
</style>
