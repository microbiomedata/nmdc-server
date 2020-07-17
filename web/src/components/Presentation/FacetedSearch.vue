<template>
  <div>
    <v-text-field
      v-model="filterText"
      solo
      label="search"
      clearable
      class="px-2"
      dense
      hide-details
      outlined
      flat
      append-icon="mdi-magnify"
    />
    <v-list
      ref="list"
      dense
      shaped
      class="compact"
    >
      <template v-for="field in filteredFields">
        <template
          v-if="!(fieldmeta[field] && (fieldmeta[field].hide || fieldmeta[field].hideFacet))"
        >
          <v-menu
            :key="field"
            offset-x
            :close-on-content-click="false"
            @input="toggleMenu(field, $event)"
          >
            <template #activator="{ on }">
              <v-list-item
                v-show="!hasActiveConditions(field)"
                v-on="on"
              >
                <v-list-item-content>
                  <v-list-item-title> {{ fieldDisplayName(field) }} </v-list-item-title>
                </v-list-item-content>
                <v-list-item-icon>
                  <v-icon> mdi-play </v-icon>
                </v-list-item-icon>
              </v-list-item>
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
        </template>
      </template>
    </v-list>
  </div>
</template>

<script>
import Vue from 'vue';

import { fieldDisplayName, valueDisplayName } from '@/util';
import * as encoding from '@/encoding';

export default {
  props: {
    type: {
      type: String,
      default: 'study',
    },
    conditions: {
      type: Array,
      default: () => [],
    },
    fields: {
      type: Array,
      default: () => [],
    },
  },
  data: () => ({
    valueCount: {},
    fieldmeta: encoding.fields,
    filterText: '',
    menuState: {},
  }),
  computed: {
    filteredFields() {
      if (this.filterText) {
        return this.fields.filter((f) => f.toLowerCase()
          .indexOf(this.filterText.toLowerCase()) >= 0);
      }
      return this.fields;
    },
  },
  methods: {
    fieldDisplayName,
    valueDisplayName,
    toggleMenu(category, value) {
      Vue.set(this.menuState, category, value);
    },
    hasActiveConditions(category) {
      return this.conditions.some((cond) => cond.field === category);
    },
  },
};
</script>
