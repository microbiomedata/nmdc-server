<script lang="ts">
import { defineComponent, type PropType } from 'vue';

import type { BaseSearchResult } from '@/data/api';
import { urlify } from '@/data/utils';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<BaseSearchResult>,
      required: true,
    },
    subtitleKey: {
      type: String as PropType<Extract<keyof BaseSearchResult, string>>,
      default: 'description',
    },
  },
  setup() {
    return { urlify };
  },
});
</script>

<template>
  <div class="mb-8">
    <div class="text-h4 mb-2">
      {{ item.annotations.title || item.name }}
    </div>

    <div class="text-body-1">
      <div v-if="$slots.subtitle">
        <slot name="subtitle" />
      </div>
      <div v-else-if="item[subtitleKey]">
        {{ item[subtitleKey] }}
      </div>
    </div>
  </div>
</template>
