<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
// import { uniqWith } from 'lodash';
import { api } from '@/data/api';
import { makeTree } from '@/util';
import SegmentConditions from '@/mixins/SegmentConditions';

export default {
  components: { Treeselect },
  mixins: [SegmentConditions],
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
  },

  methods: {
    async setSelected(nodeKeys) {
      const conditions = this.otherConditions;
      const value = nodeKeys.map((key) => {
        const treepath = {};
        let node = this.treeData.nodeMap[key];
        do {
          treepath[node.heirarchyKey] = node.label;
          node = node.parent;
        } while (node.parent);
        return treepath;
      });
      conditions.push({
        table: this.table,
        field: this.field,
        op: 'tree',
        value,
      });
      console.log(nodeKeys, conditions);
      // nodeKeys.forEach((key) => {
      //   let node = this.treeData.nodeMap[key];
      //   do {
      //     conditions.push({
      //       op: 'tree',
      //       field: node.heirarchyKey,
      //       value: node.label,
      //       table: this.table,
      //     });
      //     node = node.parent;
      //   } while (node.parent);
      // });
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
