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
    image: {
      type: String,
      default: '',
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

    function dottedValueDisplayName(dottedFieldName: string) {
      const fields = dottedFieldName.split('.');
      const field = fields[fields.length - 1];
      let intermediateValue: any = props.item;
      while (fields.length && intermediateValue !== undefined) {
        const intermediateField = fields.shift()!;
        intermediateValue = intermediateValue[intermediateField];
      }
      return valueDisplayName(field, intermediateValue);
    }

    function dottedFieldDisplayName(dottedFieldName: string) {
      const fields = dottedFieldName.split('.');
      const field = fields.pop()!;
      return fieldDisplayName(field);
    }

    function getDottedField(dottedFieldName: string) {
      const fields = dottedFieldName.split('.');
      const field = fields.pop()!;
      return getField(field);
    }

    return {
      href,
      getDottedField,
      dottedFieldDisplayName,
      dottedValueDisplayName,
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
    <img
      v-if="image"
      :src="image"
      width="160px"
      class="pr-2"
      alt="Logo"
    >
    <v-list-item-avatar v-else>
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
    target="_blank"
    rel="noopener noreferrer"
    v-on="{
      // TODO: fix warning.
      click: bindClick ? () => $emit('click') : undefined
    }"
  >
    <img
      v-if="image"
      :src="image"
      width="160px"
      class="pr-2"
      alt="Logo"
    >
    <v-list-item-avatar v-else-if="getDottedField(field)">
      <v-icon>
        {{ getDottedField(field).icon || 'mdi-text' }}
      </v-icon>
    </v-list-item-avatar>
    <v-list-item-content>
      <v-list-item-title>
        {{ dottedFieldDisplayName(field) }}
      </v-list-item-title>
      <v-list-item-subtitle
        style="white-space: initial;"
      >
        {{ dottedValueDisplayName(field, item[field]) }}
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
</template>
