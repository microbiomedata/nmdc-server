<script lang="ts">
import { defineComponent, type PropType } from 'vue';

import type { BaseSearchResult } from '@/data/api';
import { urlify } from '@/data/utils';
import PageTitle from '@/components/Presentation/PageTitle.vue';

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
  <div>
    <page-title 
      :title="item.annotations.title || item.name"
    >
      <template #subtitle>
        <div v-if="$slots.subtitle">
          <slot name="subtitle" />
        </div>
        <div v-else-if="item[subtitleKey]">
          {{ item[subtitleKey] }}
        </div>
      </template>
    </page-title>
  </div>
</template>
