<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';

import { BaseSearchResult } from '@/data/api';
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
    return { fieldDisplayName };
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
          @click="$router.go(-1)"
        >
          <v-icon>mdi-chevron-left-box</v-icon>
        </v-btn>
      </v-col>
      <v-col class="grow">
        <div class="headline">
          {{ item.annotations.title || item.name }}
        </div>
        <div
          v-if="item[subtitleKey]"
          class="subtitle-1"
        >
          <span class="font-weight-bold">{{ fieldDisplayName(subtitleKey) }}</span>
          {{ item[subtitleKey] }}
        </div>
        <slot />
      </v-col>
    </v-row>
  </v-container>
</template>
