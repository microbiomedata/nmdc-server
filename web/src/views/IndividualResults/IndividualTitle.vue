<script lang="ts">
import { defineComponent, type PropType } from 'vue';

import type { BaseSearchResult } from '@/data/api';
import { urlify } from '@/data/utils';
// @ts-ignore
import { fieldDisplayName } from '@/util';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<BaseSearchResult>,
      required: true,
    },
    subtitleKey: {
      type: String,
      default: 'description',
    },
  },
  setup() {
    return { fieldDisplayName, urlify };
  },
});
</script>

<template>
  <v-container fluid>
    <v-row class="align-center">
      <v-col cols="auto">
        <v-btn
          icon
          variant="tonal"
          color="grey-darken-2"
          size="x-large"
          :to="{name: 'Search'}"
        >
          <v-icon>mdi-chevron-left-box</v-icon>
        </v-btn>
      </v-col>
      <v-col>
        <h1 class="headline">
          {{ item.annotations.title || item.name }}
        </h1>
        <div
          v-if="item[subtitleKey]"
          class="subtitle-1"
        >
          <span class="font-weight-bold pr-1">{{ fieldDisplayName(subtitleKey) }}</span>
          <span v-html="urlify(item[subtitleKey] as string)" />
        </div>
        <slot />
      </v-col>
    </v-row>
  </v-container>
</template>
