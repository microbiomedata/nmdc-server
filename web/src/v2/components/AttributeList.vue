<script lang="ts">
import { computed, defineComponent, PropType } from '@vue/composition-api';
import { isObject } from 'lodash';

import { BaseSearchResult } from '@/data/api';
import { getField } from '@/encoding';
import { fieldDisplayName, valueDisplayName } from '@/util';

export default defineComponent({
  props: {
    type: {
      type: String,
      default: '',
    },
    item: {
      type: Object as PropType<BaseSearchResult>,
      required: true,
    },
  },

  setup(props) {
    const displayFields = computed(() => {
      const ret = Object.keys(props.item).filter((field) => {
        const value = props.item[field];
        if (['name', 'description'].includes(field)) {
          return false;
        }
        return !isObject(value) && value && (!getField(field) || !getField(field).hideAttr);
      });
      return ret;
    });

    const alternateIdentifiers = computed(() => props.item.alternate_identifiers
      .map((id) => [id, `https://identifiers.org/${id}`]));

    function href(field: string) {
      if (field.startsWith('open_in_')) {
        return props.item[field];
      }
      const value = props.item[field] as string;
      if (typeof value === 'string' && value.startsWith('http')) {
        return props.item[field];
      }
      return undefined;
    }

    return {
      // computed
      alternateIdentifiers,
      displayFields,
      // methods
      getField,
      href,
      fieldDisplayName,
      valueDisplayName,
    };
  },
});
</script>

<template>
  <div class="ma-6">
    <div class="display-1">
      Attributes
    </div>
    <v-list
      style="column-count: 3;"
      class="d-block py-4"
    >
      <v-col
        v-for="field in displayFields"
        :key="field"
        class="pa-0 d-inline-block"
      >
        <v-list-item
          :href="href(field)"
          target="_blank"
        >
          <v-list-item-avatar>
            <v-icon v-if="getField(field)">
              {{ getField(field).icon || 'mdi-text' }}
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
      </v-col>
    </v-list>
    <v-list v-if="alternateIdentifiers.length > 0">
      <div class="display-1">
        Alternate Identifiers
      </div>
      <v-list-item
        v-for="link in alternateIdentifiers"
        :key="link[0]"
        :href="link[1]"
      >
        <v-list-item-avatar>
          <v-icon>mdi-link</v-icon>
        </v-list-item-avatar>
        <v-list-item-content>
          <v-list-item-title>
            {{ link[0] }}
          </v-list-item-title>
          <v-list-item-subtitle>
            {{ link[1] }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </div>
</template>
