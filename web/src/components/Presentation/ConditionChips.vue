<script>
import moment from 'moment';
import Vue from 'vue';
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
    valueTransform(val, type) {
      // If it's not primitive
      if (typeof val === 'object') {
        const inner = val.map((v) => this.valueTransform(v, type)).join(', ');
        return `(${inner})`;
      }
      // If it will parse strictly as a number;
      if (!Number.isNaN(Number(val))) {
        return val;
      }
      // If it parses as a date;
      if (!Number.isNaN(Date.parse(val))) {
        return moment(val).format('MM/DD/YYYY');
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
          @click:close="$emit('remove', cond)"
        >
          {{ valueTransform(cond.value, '') }}
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
  border-left: 1px solid gray;
  border-radius: 0 !important;
  cursor: pointer;
}
</style>
