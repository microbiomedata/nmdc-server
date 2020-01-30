<template>
  <div v-if="!singleton">
    <v-pagination
      v-model="page"
      :length="Math.ceil(results.length / 10)"
      :total-visible="7"
    />
    <v-list
      dense
      two-line
    >
      <template v-for="(result, resultIndex) in results.slice(10*(page-1), 10*page)">
        <v-divider
          v-if="resultIndex > 0"
          :key="`${result.id}-divider`"
        />
        <v-list-item
          :key="result.id"
          @click="$emit('selected', { value: result.id })"
        >
          <v-list-item-avatar>
            <v-icon
              v-text="types[type].icon"
            />
          </v-list-item-avatar>
          <v-list-item-content>
            <v-list-item-title>
              {{ result.name }}
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ result.description || 'No description' }}
            </v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-list>
  </div>
  <div v-else>
    <v-card>
      <v-container fluid>
        <v-row>
          <v-col class="flex-grow-0 pr-0">
            <v-icon
              x-large
            >
              {{ types[type].icon }}
            </v-icon>
          </v-col>
          <v-col class="flex-grow-1">
            <div class="headline">
              {{ results[0].name }}
            </div>
            <div>{{ results[0].description }}</div>
            <v-list>
              <v-tooltip
                v-for="field in displayFields"
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
                        {{ valueDisplayName(field, results[0][field]) }}
                      </v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </template>
                <span>Click to select {{ typeWithCardinality(type, 2) }} with this value</span>
              </v-tooltip>
            </v-list>
            <template v-for="relatedType in ['study', 'project', 'sample']">
              <v-btn
                v-if="type !== relatedType"
                :key="relatedType"
                outlined
                class="mr-3"
                @click="$emit('selected', {
                  type: relatedType,
                  field: `${type}_id`,
                  value: results[0].id,
                })"
              >
                <v-icon left>
                  {{ types[relatedType].icon }}
                </v-icon>
                {{ relatedTypeDescription(relatedType) }}
              </v-btn>
            </template>
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </div>
</template>
<script>
import { isObject } from 'lodash';

import {
  typeWithCardinality, valueCardinality, fieldDisplayName, valueDisplayName,
} from '../util';
import { types, fields } from './encoding';

export default {
  props: {
    type: {
      type: String,
      default: 'study',
    },
    results: {
      type: Array,
      default: () => [],
    },
    conditions: {
      type: Array,
      default: () => [],
    },
  },
  data: () => ({
    page: 1,
    types,
    fields,
  }),
  computed: {
    singleton() {
      return this.results.length === 1 && this.conditions.findIndex((cond) => cond.field === 'id' && cond.op === '==') >= 0;
    },
    childType() {
      const childTypes = {
        study: 'project',
        project: 'sample',
      };
      return childTypes[this.type];
    },
    parentType() {
      const parentTypes = {
        project: 'study',
        sample: 'project',
      };
      return parentTypes[this.type];
    },
    displayFields() {
      return Object.keys(this.results[0]).filter((field) => {
        const value = this.results[0][field];
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
      this.$emit('unselected', { value: this.results[0].id });
      this.$emit('selected', { field, value: this.results[0][field] });
    },
    relatedTypeDescription(relatedType) {
      const n = valueCardinality(this.results[0][`${relatedType}_id`]);
      return `${n} ${typeWithCardinality(relatedType, n)}`;
    },
  },
};
</script>
