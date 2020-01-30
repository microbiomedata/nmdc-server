<template>
  <v-list
    ref="list"
    dense
    class="compact"
  >
    <template v-for="facet in facets">
      <v-subheader :key="facet.field">
        {{ fieldDisplayName(facet.field) }}
      </v-subheader>
      <v-list-item-group
        :key="`${facet.field}-item`"
        v-model="selected[facet.field]"
        multiple
      >
        <v-list-item
          v-for="val in facet.values.slice(0, valueCount[facet.field])"
          :key="val.value"
          :disabled="val.count === 0"
          :value="val.value"
          class="overflow"
        >
          <v-list-item-content>
            {{ valueDisplayName(facet.field, val.value) }}
          </v-list-item-content>
          <v-list-item-action>
            <v-list-item-action-text v-text="val.count" />
          </v-list-item-action>
        </v-list-item>
      </v-list-item-group>
      <v-list-item
        v-if="valueCount[facet.field] < facet.values.length"
        :key="`${facet.field}-more`"
        @click="valueCount[facet.field] += 10"
      >
        <v-list-item-content
          class="blue--text text--darken-4 caption"
        >
          more
        </v-list-item-content>
      </v-list-item>
      <v-list-item
        v-if="valueCount[facet.field] > 5"
        :key="`${facet.field}-less`"
        @click="valueCount[facet.field] = 5"
      >
        <v-list-item-content
          class="blue--text text--darken-4 caption"
        >
          less
        </v-list-item-content>
      </v-list-item>
    </template>
  </v-list>
</template>
<script>
import { fieldDisplayName, valueDisplayName } from '../util';
import DataAPI from '../data/DataAPI';

const api = new DataAPI();
export default {
  props: {
    type: {
      type: String,
      default: 'study',
    },
    value: {
      type: Array,
      default: () => [],
    },
  },
  data: () => ({
    facets: [],
    selected: {},
    valueCount: {},
  }),
  computed: {
    conditions() {
      return this.value;
    },
  },
  watch: {
    type() {
      this.$refs.list.$el.parentNode.scrollTop = 0;
      this.initializeType();
      this.updateResults();
    },
    selected: {
      handler() {
        const cond = [];
        Object.keys(this.selected).forEach((field) => {
          this.selected[field].forEach((value) => {
            cond.push({ field, op: '==', value });
          });
        });
        this.$emit('input', cond);
      },
      deep: true,
    },
    conditions() {
      // First check for equivalence no-op to avoid update loop
      let same = true;
      this.conditions.forEach((condition) => {
        if (this.selected[condition.field] === undefined) {
          // A field that faceted search cannot track (e.g. array field)
          return;
        }
        if (condition.op === '==' && !this.selected[condition.field].includes(condition.value)) {
          same = false;
        }
      });
      Object.keys(this.selected).forEach((field) => {
        this.selected[field].forEach((value) => {
          if (!this.conditions.find((cond) => cond.field === field && cond.op === '==' && cond.value === value)) {
            same = false;
          }
        });
      });

      if (!same) {
        const sel = {};
        Object.keys(this.selected).forEach((field) => { sel[field] = []; });
        this.conditions.forEach((condition) => {
          if (condition.op === '==') {
            if (sel[condition.field] === undefined) {
              // A field that faceted search cannot track (e.g. array field)
              return;
            }
            sel[condition.field].push(condition.value);
          }
          // Don't know what to do with non-equality condition
        });
        this.selected = sel;
      }
      this.updateResults();
    },
  },
  created() {
    this.initializeType();
    this.updateResults();
  },
  methods: {
    initializeType() {
      this.selected = {};
      this.valueCount = {};
      api.primitiveFields(this.type).forEach((field) => {
        this.$set(this.selected, field, []);
        this.$set(this.valueCount, field, 5);
      });
    },
    updateResults() {
      this.facets = api.primitiveFields(this.type)
        .map((field) => ({
          field,
          values: api.facetSummary(this.type, field, this.conditions),
        }));
    },
    fieldDisplayName,
    valueDisplayName,
  },
};
</script>
<style scoped>
.overflow {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.v-list--dense.compact .v-list-item {
  min-height: 10px;
}
.v-list--dense.compact .v-list-item .v-list-item__content {
  padding: 0;
}
.v-list--dense.compact .v-list-item .v-list-item__action {
  margin: 0 0 0 16px;
}
</style>
