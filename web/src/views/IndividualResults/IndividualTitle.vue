<script lang="ts">
import { defineComponent, PropType } from 'vue';

import { BaseSearchResult } from '@/data/api';
import { urlify } from '@/data/utils';
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
    <v-row>
      <v-col class="shrink">
        <v-btn
          icon
          x-large
          :to="{name: 'Search'}"
        >
          <v-icon>mdi-chevron-left-box</v-icon>
        </v-btn>
      </v-col>
      <v-col class="grow">
        <div class="text-h5">
          {{ item.annotations.title || item.name }}
        </div>
        <div
          v-if="item[subtitleKey]"
          class="text-subtitle-1"
        >
          <span class="font-weight-bold pr-1">{{ fieldDisplayName(subtitleKey) }}</span>
          <span v-html="urlify(item[subtitleKey])" />
        </div>
        <slot />
      </v-col>
    </v-row>
  </v-container>
</template>
