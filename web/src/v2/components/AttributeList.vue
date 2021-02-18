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
        return !isObject(value) && value;
      });
      return ret;
    });

    return {
      // computed
      displayFields,
      // methods
      getField,
      fieldDisplayName,
      valueDisplayName,
    };
  },
});
</script>

<template>
  <div>
    <div class="display-1 mt-4 mb-2">
      Item Attributes
    </div>
    <v-list>
      <template v-for="field in displayFields">
        <template
          v-if="!getField(field)
            || (getField(field).hideFacet && !getField(field).hideAttr)"
        >
          <v-list-item
            :key="field"
            @click="selectField(type, field)"
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
        </template>
      </template>
    </v-list>
  </div>
</template>
