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
            @input="toggleMenu(field, $event)"
          >
            <template #activator="{ on }">
              <v-list-item v-on="on">
                <v-list-item-content>
                  <v-list-item-title> {{ fieldDisplayName(field) }} </v-list-item-title>
                </v-list-item-content>
                <v-list-item-icon>
                  <v-icon> mdi-play </v-icon>
                </v-list-item-icon>
              </v-list-item>
            </template>
            <v-card width="500">
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
  <!-- <v-list-item
            v-for="val in values.slice(0, valueCount[field])"
            :key="val.facet"
            :disabled="val.count === 0"
            :value="val.facet"
            class="overflow"
          >
            <v-list-item-content>
              {{ valueDisplayName(field, val.facet) }}
            </v-list-item-content>
            <v-list-item-action>
              <v-list-item-action-text v-text="val.count" />
            </v-list-item-action>
          </v-list-item>
        </v-list-item-group>
        <v-list-item
          v-if="valueCount[field] < values.length"
          :key="`${field}-more`"
          @click="valueCount[field] += 10"
        >
          <v-list-item-content
            class="blue--text text--darken-4 caption"
          >
            more
          </v-list-item-content>
        </v-list-item>
        <v-list-item
          v-if="valueCount[field] > 5"
          :key="`${field}-less`"
          @click="valueCount[field] = 5"
        >
          <v-list-item-content
            class="blue--text text--darken-4 caption"
          >
            less
          </v-list-item-content>
        </v-list-item> -->
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
        return this.fields.filter((f) => f.indexOf(this.filterText) >= 0);
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
  },
};
</script>
