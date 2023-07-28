<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';
import { getField } from '@/encoding';
import { fieldDisplayName, valueDisplayName } from '@/util';
import { BaseSearchResult, BiosampleSearchResult } from '@/data/api';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<BaseSearchResult | BiosampleSearchResult>,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    index: {
      type: Number,
      required: false,
      default: -1,
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
    displayName: {
      type: String,
      required: false,
      default: '',
    },
  },

  setup(props) {
    function getValue(field: string) {
      if (field === 'geo_loc_name') {
        return props.item.annotations.geo_loc_name;
      }
      if (field === 'biosample_categories') {
        return (props.item?.annotations.biosample_categories as string[]).join(', ');
      }
      if (
        field === 'env_broad_scale'
          || field === 'env_local_scale'
          || field === 'env_medium'
      ) {
        const item = props.item as BiosampleSearchResult;
        const env = item[field];
        return `${env.label} (${env.id})`;
      }
      if (field === 'emsl_biosample_identifiers') {
        const item = props.item as BiosampleSearchResult;
        return item.emsl_biosample_identifiers[props.index] || '';
      }
      return valueDisplayName(field, props.item[field]);
    }

    function href(field: string) {
      if (field.startsWith('open_in_')) {
        return props.item[field];
      }
      const value = props.item[field] as string;
      if (typeof value === 'string' && value.startsWith('http')) {
        return props.item[field];
      }
      if (field === 'study_id') {
        return `/details/study/${props.item.study_id}`;
      }
      return undefined;
    }

    return {
      getField,
      fieldDisplayName,
      getValue,
      href,
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
    :target="field==='study_id' ? '' : '_blank' "
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
    <v-list-item-avatar v-else-if="getField(field)">
      <v-icon>
        {{ getField(field).icon || 'mdi-text' }}
      </v-icon>
    </v-list-item-avatar>
    <v-list-item-content>
      <v-list-item-title>
        {{ displayName.length > 0 ? displayName : fieldDisplayName(field) }}
      </v-list-item-title>
      <v-list-item-subtitle
        style="white-space: initial;"
      >
        {{ getValue(field) }}
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
</template>
