<script>
import moment from 'moment';
import Vue from 'vue';
import { mapGetters } from 'vuex';
import { groupBy } from 'lodash';
import { opMap } from '@/data/api';
import { fieldDisplayName } from '@/util';

export default {
  props: {
    conditions: {
      // api.Condition[]
      type: Array,
      required: true,
    },
  },

  data: () => ({ menuState: {} }),

  computed: {
    ...mapGetters(['typeSummary']),
    conditionGroups() {
      return Object.entries(groupBy(
        this.conditions,
        (c) => JSON.stringify(({ field: c.field, table: c.table })),
      )).map(([group, conditions]) => {
        const parsed = JSON.parse(group);
        return {
          key: parsed.field + parsed.table,
          field: parsed.field,
          table: parsed.table,
          conditions,
        };
      });
    },
  },

  methods: {
    fieldDisplayName,
    verb(op) {
      return opMap[op];
    },
    valueTransform(cond, val, field, type) {
      // If it's not primitive
      if (val && typeof val === 'object') {
        const inner = val.map((v) => this.valueTransform(v, field, type)).join(', ');
        return `(${inner})`;
      }
      const summary = this.typeSummary(type)[field];
      if (summary) {
        if (['float', 'number', 'string'].includes(summary.type)) {
          return val;
        }
        if (['date'].includes(summary.type)) {
          return moment(val).format('MM/DD/YYYY');
        }
        throw new Error(`Unknown entity type for ${type}: ${field}: ${summary.type}`);
      }
      return val;
    },
    toggleMenu(category, value) {
      Vue.set(this.menuState, category, value);
    },
  },
};
</script>

<template>
  <div>
    <v-card
      v-for="group in conditionGroups"
      :key="group.key"
      class="d-flex flex-row pa-1 my-2"
      color="primary lighten-5"
    >
      <div style="width: 94%">
        <span class="text-subtitle-2">
          {{ fieldDisplayName(group.field) }}
        </span>
        <span class="text-caption">
          [{{ verb(group.conditions[0].op) }}]
        </span>
        <v-chip
          v-for="cond in group.conditions"
          :key="JSON.stringify(cond.value)"
          small
          close
          label
          class="ma-1"
          style="max-width: 90%;"
          @click:close="$emit('remove', cond)"
        >
          <span class="chip-content">
            {{ valueTransform(cond, cond.value, cond.field, cond.table) }}
          </span>
        </v-chip>
      </div>
      <v-menu
        offset-x
        top
        :close-on-content-click="false"
        @input="toggleMenu(group.key, $event)"
      >
        <template #activator="{ on }">
          <div
            class="expand d-flex flex-column justify-center"
            style="width: 6%"
            v-on="on"
          >
            <v-icon small>
              mdi-play
            </v-icon>
          </div>
        </template>
        <v-card
          width="500"
        >
          <slot
            name="menu"
            v-bind="{
              field: group.field,
              table: group.table,
              isOpen: menuState[group.key],
            }"
          />
        </v-card>
      </v-menu>
    </v-card>
  </div>
</template>

<style scoped>
.expand {
  border-left: 1px solid grey;
  border-radius: 0 !important;
  cursor: pointer;
}
.chip-content {
  overflow: hidden;
}
</style>
