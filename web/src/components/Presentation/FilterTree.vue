<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { api } from '@/data/api';
import { makeTree } from '@/util';

export default {
  components: { Treeselect },

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
      const conditions = [
        ...this.otherConditions,
        ...nodeKeys.map((key) => ({
          op: '==',
          field: this.treeData.nodeMap[key].heirarchyKey,
          value: this.treeData.nodeMap[key].label,
          table: this.table,
        })),
      ];
      this.$store.dispatch('route', { conditions });
    },
  },
};
</script>

<template>
  <div class="tree-overflow">
    <treeselect
      :options="tree"
      multiple
      always-open
      class="ma-2"
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
