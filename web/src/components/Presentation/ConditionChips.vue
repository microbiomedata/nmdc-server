<script>
import Vue from 'vue';
import { groupBy } from 'lodash';

import { fieldDisplayName, valueDisplayName } from '@/util';

export default {
  props: {
    conditions: {
      type: Array,
      required: true,
    },
  },

  data: () => ({ menuState: {} }),

  computed: {
    conditionGroups() {
      return groupBy(this.conditions, (c) => c.field);
    },
  },

  methods: {
    fieldDisplayName,
    valueDisplayName,
    verb(op) {
      switch (op) {
        case '==':
          return 'is';
        default:
          return op;
      }
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
      v-for="(conds, field) in conditionGroups"
      :key="field"
      class="d-flex flex-row pa-1 my-2"
      color="primary lighten-5"
    >
      <div style="width: 94%">
        <span class="text-subtitle-2">
          {{ fieldDisplayName(field) }}
        </span>
        <span class="text-caption">
          [{{ verb(conds[0].op) }}]
        </span>
        <v-chip
          v-for="cond in conds"
          :key="cond.value"
          small
          close
          label
          class="ma-1"
          @click:close="$emit('remove', cond)"
        >
          {{ cond.value }}
        </v-chip>
      </div>
      <v-menu
        offset-x
        :close-on-content-click="false"
        @input="toggleMenu(field, $event)"
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
          max-height="90vh"
        >
          <slot
            name="menu"
            v-bind="{ field, isOpen: menuState[field] }"
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
