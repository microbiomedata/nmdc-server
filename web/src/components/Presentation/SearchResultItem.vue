<script setup lang="ts">
import { BaseSearchResult } from '@/data/api';

interface Props {
  titleKey?: string;
  subtitleKey?: string;
  result: BaseSearchResult;
  icon?: string;
}

withDefaults(defineProps<Props>(), {
  titleKey: 'name',
  subtitleKey: 'description',
  icon: 'mdi-book',
});
</script>

<template>
  <v-list-item
    :ripple="false"
    :active="false"
    :link="false"
  >
    <template #prepend>
      <slot
        name="prepend-action"
        v-bind="{ result }"
      />
      <v-icon>
        {{
          result.children && Array.isArray(result.children) && result.children.length > 0 && result.study_category === 'research_study'
            ? 'mdi-book-multiple-outline'
            : icon
        }}
      </v-icon>
    </template>

    <v-list-item-title>
      <div class="d-flex align-center">
        <div class="text-subtitle-2">
          {{ result[titleKey] }}
        </div>
      </div>
    </v-list-item-title>
    <v-list-item-subtitle>
      <slot
        name="subtitle"
        v-bind="{ result }"
      >
        {{ result[subtitleKey] || 'No description' }}
      </slot>
    </v-list-item-subtitle>
    <slot
      name="item-content"
      v-bind="{ result }"
    />

    <template #append>
      <slot
        name="action-right"
        v-bind="{ result }"
      />
    </template>
  </v-list-item>
</template>