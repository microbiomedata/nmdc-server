<script>
import Vue from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { uniqWith } from 'lodash';
import { api } from '@/data/api';
import { makeTree } from '@/util';

export default Vue.extend({
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
    value: [],
  }),

  asyncComputed: {
    data() { return api.getEnvironmentSankeyAggregation(this.otherConditions); },
  },

  computed: {
    treeData() {
      return makeTree(this.data || [], this.heirarchy);
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
    myConditions() {
      return this.conditions
        .filter((c) => (this.heirarchy.includes(c.field)) && c.table === this.table);
    },
  },

  watch: {
    // treeData({ topoSort }) {
    //   if (topoSort) {
    //     const sel = [];
    //     this.myConditions.forEach((c) => {
    //       const node = this.treeData.topoSort
    //         .find((n) => n.name === c.value && n.heirarchyKey === c.field);
    //       sel.push(getChain(node)
    //         .filter((n) => n.id !== '')
    //         .map((n) => n.name)
    //         .join('.'));
    //     });
    //     this.value = sel;
    //   }
    // },
  },

  methods: {
    async setSelected(nodeKeys) {
      const conditions = this.otherConditions;
      nodeKeys.forEach((key) => {
        let node = this.treeData.nodeMap[key];
        do {
          conditions.push({
            op: '==',
            field: node.heirarchyKey,
            value: node.label,
            table: this.table,
          });
          node = node.parent;
        } while (node.parent);
      });
      this.$emit('select', {
        conditions: uniqWith(conditions, (a, b) => a.field === b.field && a.value === b.value),
      });
    },
  },
});
</script>

<template>
  <div class="tree-overflow">
    <treeselect
      :options="tree"
      multiple
      always-open
      class="ma-2"
      :value="value"
      @input="setSelected"
    >
      <template #option-label="{ node }">
        <span> {{ node.label }} ({{ node.raw.count }}) </span>
      </template>
    </treeselect>
  </div>
</template>

<style lang="scss" scoped>
.tree-overflow {
  max-height: 475px;
  height: 475px;
  overflow-y: auto;
}
</style>
