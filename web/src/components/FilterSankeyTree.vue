<script>
import { defineComponent } from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { uniqWith } from 'lodash';
import { api } from '@/data/api';
import { makeTree } from '@/util';

export default defineComponent({
  name: 'FilterSankeyTree',
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
    createdDelay: false,
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

  created() {
    /* Enable loading bar after 2 seconds of no load, to avoid overly noisy facet dialogs */
    window.setTimeout(() => { this.createdDelay = true; }, 2000);
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
    <v-progress-linear
      v-if="data === null && createdDelay"
      indeterminate
      style="position: absolute;"
    />
    <treeselect
      :options="tree"
      multiple
      always-open
      class="ma-2 mt-4"
      :max-height="425"
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
  max-height: 525px;
  height: 525px;
  overflow-y: auto;
}
</style>
