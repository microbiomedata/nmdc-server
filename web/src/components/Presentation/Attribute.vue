<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';
import { getField } from '@/encoding';
import { fieldDisplayName, valueDisplayName } from '@/util';
import { BaseSearchResult } from '@/data/api';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<BaseSearchResult>,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    link: {
      type: Object as PropType<{ name: string; target: string; } | null>,
      default: null,
    },
    bindClick: {
      type: Boolean,
      default: false,
    },
  },

  setup(props) {
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
      href,
      getField,
      fieldDisplayName,
      valueDisplayName,
    };
  },
});
</script>

<template>
  <v-list-item
    v-if="link"
    :key="link.name"
    :href="link.target"
  >
    <v-list-item-avatar>
      <v-icon>mdi-link</v-icon>
    </v-list-item-avatar>
    <v-list-item-content>
      <v-list-item-title>
        {{ link.name }}
      </v-list-item-title>
      <v-list-item-subtitle>
        {{ link.target }}
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
  <v-list-item
    v-else
    :href="href(field)"
    :to="to"
    target="_blank"
    v-on="{
      click: bindClick ? () => $emit('click') : undefined
    }"
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
      <v-list-item-subtitle style="text-overflow: unset; overflow-wrap: break-word;">
        {{ valueDisplayName(field, item[field]) }}
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
</template>
