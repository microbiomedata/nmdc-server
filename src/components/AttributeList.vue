<template>
  <div>
    <template v-for="relatedType in ['study', 'project', 'sample', 'data_object']">
      <v-btn
        v-if="type !== relatedType"
        :key="relatedType"
        outlined
        class="mr-3"
        @click="$emit('selected', {
          type: relatedType,
          field: `${type}_id`,
          value: item.id,
        })"
      >
        <v-icon left>
          {{ types[relatedType].icon }}
        </v-icon>
        {{ relatedTypeDescription(relatedType) }}
      </v-btn>
    </template>
    <v-list>
      <v-list-item v-if="item.ecosystem">
        <v-list-item-avatar>
          <v-icon>mdi-text</v-icon>
        </v-list-item-avatar>
        <v-list-item-content>
          <v-list-item-title>
            Ecosystem
          </v-list-item-title>
          <v-list-item-subtitle>
            {{ item.ecosystem }}
            >
            {{ item.ecosystem_category }}
            >
            {{ item.ecosystem_type }}
            >
            {{ item.ecosystem_subtype }}
            >
            {{ item.specific_ecosystem }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <template v-for="field in displayFields">
        <template v-if="!fields[field] || !fields[field].hide">
          <v-tooltip
            v-if="field.startsWith('open_')"
            :key="field"
            bottom
          >
            <template v-slot:activator="{ on }">
              <v-list-item
                @click="openLink(item[field])"
                v-on="on"
              >
                <v-list-item-avatar>
                  <v-icon>
                    mdi-open-in-new
                  </v-icon>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title>
                    {{ fieldDisplayName(field) }}
                  </v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </template>
            <span>Click to follow link</span>
          </v-tooltip>
          <v-tooltip
            v-else
            :key="field"
            bottom
          >
            <template v-slot:activator="{ on }">
              <v-list-item
                @click="selectField(field)"
                v-on="on"
              >
                <v-list-item-avatar>
                  <v-icon>
                    {{ fields[field] ? fields[field].icon : 'mdi-text' }}
                  </v-icon>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title>
                    {{ fieldDisplayName(field) }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ valueDisplayName(field, item[field]) }}
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </template>
            <span>Click to select {{ typeWithCardinality(type, 2) }} with this value</span>
          </v-tooltip>
        </template>
      </template>
    </v-list>
  </div>
</template>
<script>
import { isObject } from 'lodash';

import {
  typeWithCardinality, valueCardinality, fieldDisplayName, valueDisplayName,
} from '../util';
import { types, fields } from '../encoding';

export default {
  props: {
    type: {
      type: String,
      default: '',
    },
    item: {
      type: Object,
      default: () => {},
    },
  },
  data: () => ({
    types,
    fields,
  }),
  computed: {
    displayFields() {
      return Object.keys(this.item).filter((field) => {
        const value = this.item[field];
        if (['name', 'description'].includes(field)) {
          return false;
        }
        return !isObject(value);
      });
    },
  },
  methods: {
    fieldDisplayName,
    valueDisplayName,
    typeWithCardinality,
    selectField(field) {
      this.$emit('unselected', { value: this.item.id });
      this.$emit('selected', { field, value: this.item[field] });
    },
    relatedTypeDescription(relatedType) {
      const n = valueCardinality(this.item[`${relatedType}_id`]);
      return `${n} ${typeWithCardinality(relatedType, n)}`;
    },
    openLink(url) {
      window.open(url, '_blank');
    },
  },
};
</script>
