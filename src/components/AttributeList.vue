<template>
  <div>
    <template v-for="(relatedType, relatedTypeIndex) in relatedTypes">
      <v-btn
        v-if="type !== relatedType.type && relatedTypeCount(relatedType) > 0"
        :key="relatedTypeIndex"
        outlined
        class="mr-3"
        @click="$emit('selected', {
          type: relatedType.type,
          conditions: relatedTypeConditions(relatedType),
        })"
      >
        <v-icon left>
          {{ types[relatedType.type].icon }}
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
            <span
              v-for="(field, fieldIndex) in ecosystemFields"
              :key="field"
              class="primary--text"
              style="cursor: pointer"
              @click="selectField(field)"
            >
              <v-icon
                v-if="fieldIndex > 0"
                small
              >
                mdi-chevron-right
              </v-icon>
              {{ item[field] }}
            </span>
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
  typeWithCardinality, fieldDisplayName, valueDisplayName,
} from '../util';
import { types, fields } from '../encoding';
import api from '../data/api';

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
    ecosystemFields: [
      'ecosystem',
      'ecosystem_category',
      'ecosystem_type',
      'ecosystem_subtype',
      'specific_ecosystem',
    ],
    relatedTypes: [
      { type: 'study' },
      { type: 'project', conditions: [{ field: 'omics_type', op: '==', value: 'Metagenome' }] },
      { type: 'project', conditions: [{ field: 'omics_type', op: '==', value: 'Metatranscriptome' }] },
      { type: 'sample' },
      { type: 'data_object' },
    ],
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
      this.$emit('selected', {
        type: this.type,
        conditions: [{ field, op: '==', value: this.item[field] }],
      });
    },
    relatedTypeConditions(relatedType) {
      return [
        {
          field: `${this.type}_id`,
          op: '==',
          value: this.item.id,
        },
        ...(relatedType.conditions || []),
      ];
    },
    relatedTypeCount(relatedType) {
      return api.query(relatedType.type, this.relatedTypeConditions(relatedType)).length;
    },
    relatedTypeDescription(relatedType) {
      const n = this.relatedTypeCount(relatedType);
      if (relatedType.conditions && relatedType.conditions.length > 0) {
        return `${n} ${typeWithCardinality(relatedType.conditions[0].value, n)}`;
      }
      return `${n} ${typeWithCardinality(relatedType.type, n)}`;
    },
    openLink(url) {
      window.open(url, '_blank');
    },
  },
};
</script>
