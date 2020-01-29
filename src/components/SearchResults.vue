<template>
  <div v-if="results.length > 1">
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
          @click="$emit('selected', { type, id: result.id })"
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
              <v-list-item
                v-for="field in displayFields"
                :key="field"
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
            </v-list>
            <v-list v-if="childType">
              <v-list-item
                v-for="child in results[0][childType]"
                :key="child.id"
                @click="$emit('selected', { type: childType, id: child.id })"
              >
                <v-list-item-avatar>
                  <v-icon
                    v-text="types[childType].icon"
                  />
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title>
                    {{ child.name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ child.description || 'No description' }}
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
            <v-list v-if="parentType && results[0].part_of">
              <v-list-item
                @click="$emit('selected', { type: parentType, id: results[0].part_of.id })"
              >
                <v-list-item-avatar>
                  <v-icon
                    v-text="types[parentType].icon"
                  />
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title>
                    {{ results[0].part_of.name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ results[0].part_of.description || 'No description' }}
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </div>
</template>
<script>
import { isObject } from 'lodash';

import { fieldDisplayName, valueDisplayName } from '../util';
import encoding from './encoding';

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
  },
  data: () => ({
    page: 1,
    types: encoding.type,
    fields: {
      location: {
        icon: 'mdi-earth',
      },
      latitude: {
        icon: 'mdi-earth',
      },
      longitude: {
        icon: 'mdi-earth',
      },
      sample_collection_site: {
        icon: 'mdi-earth',
      },
      geographic_location: {
        icon: 'mdi-earth',
      },
      add_date: {
        icon: 'mdi-calendar',
      },
      mod_date: {
        icon: 'mdi-calendar',
      },
      ecosystem: {
        icon: 'mdi-pine-tree',
      },
      ecosystem_category: {
        icon: 'mdi-pine-tree',
      },
      ecosystem_type: {
        icon: 'mdi-pine-tree',
      },
      ecosystem_subtype: {
        icon: 'mdi-pine-tree',
      },
      specific_ecosystem: {
        icon: 'mdi-pine-tree',
      },
      ecosystem_path_id: {
        icon: 'mdi-pine-tree',
      },
      habitat: {
        icon: 'mdi-pine-tree',
      },
      community: {
        icon: 'mdi-google-circles-communities',
      },
    },
  }),
  computed: {
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
  },
};
</script>
