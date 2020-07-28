<template>
  <div>
    <v-text-field
      v-model="filterText"
      solo
      label="search"
      clearable
      class="mx-3"
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
      <div
        v-for="[groupname, filteredFields] in groupedFields"
        :key="groupname"
      >
        <v-subheader
          v-show="groupedFields.length > 1 && filteredFields.length > 0"
        >
          {{ groupname !== 'undefined' ? groupname : 'Other' }}
        </v-subheader>
        <template v-for="field in filteredFields">
          <v-menu
            :key="field.key"
            offset-x
            :close-on-content-click="false"
            @input="toggleMenu(field.key, $event)"
          >
            <template #activator="{ on }">
              <v-list-item
                v-show="!hasActiveConditions(field.key)"
                v-on="on"
              >
                <v-list-item-content>
                  <v-list-item-title> {{ fieldDisplayName(field.key) }} </v-list-item-title>
                </v-list-item-content>
                <v-list-item-icon>
                  <v-icon> mdi-play </v-icon>
                </v-list-item-icon>
              </v-list-item>
            </template>
            <v-card
              width="500"
            >
              <slot
                name="menu"
                v-bind="{
                  field: field.key,
                  isOpen: menuState[field.key],
                }"
              />
            </v-card>
          </v-menu>
        </template>
      </div>
    </v-list>
  </div>
</template>

<script>
import Vue from 'vue';
import { groupBy } from 'lodash';
import { fieldDisplayName } from '@/util';
import * as encoding from '@/encoding';

export default {
  props: {
    type: {
      type: String,
      default: 'study',
    },
    conditions: {
      type: Array,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  data: () => ({
    valueCount: {},
    fieldmeta: encoding.fields,
    filterText: '',
    menuState: {},
  }),
  computed: {
    _filteredFields() {
      if (this.filterText) {
        return this.fields.filter((f) => f.toLowerCase()
          .indexOf(this.filterText.toLowerCase()) >= 0);
      }
      return this.fields;
    },
    groupedFields() {
      const fieldsWithMeta = this._filteredFields
        .map((f) => ({ key: f, ...encoding.fields[f] }))
        .filter((f) => !f.hideFacet);
      return Object.entries(groupBy(fieldsWithMeta, 'group')).sort((a) => ((a[0] === 'undefined') ? 0 : -1));
    },
  },
  methods: {
    fieldDisplayName,
    toggleMenu(category, value) {
      Vue.set(this.menuState, category, value);
    },
    hasActiveConditions(category) {
      return this.conditions.some((cond) => cond.field === category);
    },
  },
};
</script>
