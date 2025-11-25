<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { getField } from '@/encoding';
// @ts-ignore
import { fieldDisplayName, formatBiosampleDepth, valueDisplayName } from '@/util';
import { BaseSearchResult, BiosampleSearchResult } from '@/data/api';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<BaseSearchResult | BiosampleSearchResult>,
      required: true,
    },
    field: {
      type: String,
      required: false,
      default: '',
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
  emits: ['click'],
  setup(props) {
    function getValue(field: string) {
      // For the "depth" field, format it as a string or `null`.
      // Note: I assert some types here to work around the inaccurate type definitions in `api.ts`.
      if (field === 'depth') {
        return formatBiosampleDepth(props.item.annotations?.depth as object | null, props.item.depth as number | null);
      }
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

    function href(field: string): string | undefined {
      if (field.startsWith('open_in_')) {
        return props.item[field] as string;
      }
      const value = props.item[field] as string;
      if (typeof value === 'string' && value.startsWith('http')) {
        return props.item[field] as string;
      }
      if (field === 'study_id') {
        return `/details/study/${props.item.study_id}`;
      }
      if (
        field === 'env_broad_scale'
          || field === 'env_local_scale'
          || field === 'env_medium'
      ) {
        const item = props.item as BiosampleSearchResult;
        const env = item[field];
        const request = `http://purl.obolibrary.org/obo/${env.id.replace(':', '_')}`;
        let apiUrl = '';
        if (env.id.startsWith('ENVO')) {
          apiUrl = 'https://www.ebi.ac.uk/ols4/ontologies/envo/classes/';
        } else if (env.id.startsWith('PO')) {
          apiUrl = 'https://www.ebi.ac.uk/ols4/ontologies/po/classes/';
        } else if (env.id.startsWith('UBERON')) {
          apiUrl = 'https://www.ebi.ac.uk/ols4/ontologies/uberon/classes/';
        }
        return `${apiUrl}${encodeURIComponent(request)}`;
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
    <template #prepend>
      <img
        v-if="image"
        :src="image"
        width="160px"
        class="pr-2"
        alt="Logo"
      >
      <v-icon 
        v-else
        class="mr-4"
        color="grey"
      >
        mdi-link
      </v-icon>
    </template>
    <v-list-item-title>
      {{ link.name }}
    </v-list-item-title>
    <v-list-item-subtitle>
      {{ link.target }}
    </v-list-item-subtitle>
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
    <template #prepend>
      <img
        v-if="image"
        :src="image"
        width="160px"
        class="pr-2"
        alt="Logo"
      >
      <v-icon 
        v-else-if="getField(field)"
        class="mr-4"
        color="grey"
      >
        {{ getField(field).icon || 'mdi-text' }}
      </v-icon>
    </template>
    <v-list-item-title>
      {{ displayName.length > 0 ? displayName : fieldDisplayName(field) }}
    </v-list-item-title>
    <v-list-item-subtitle
      style="white-space: initial;"
    >
      {{ getValue(field) }}
    </v-list-item-subtitle>
  </v-list-item>
</template>

<style scoped lang="scss">
a.v-list-item {
  color: inherit;
}
</style>