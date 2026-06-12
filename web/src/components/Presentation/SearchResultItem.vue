<script setup lang="ts">
import { BiosampleSearchResult, StudySearchResult } from '@/data/api';

interface Props {
  titleKey?: string;
  result: BiosampleSearchResult | StudySearchResult;
  icon?: string;
}

withDefaults(defineProps<Props>(), {
  titleKey: 'name',
  icon: 'mdi-book-outline',
});
</script>

<template>
  <v-list-item
    class="py-2"
    :ripple="false"
    :active="false"
    :link="false"
  >
    <template #prepend>
      <slot
        name="action-left"
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
    <div class="d-flex flex-column ga-1">
      <v-list-item-title>
        <slot
          name="item-title"
          v-bind="{ result }"
        />
      </v-list-item-title>
      <v-list-item-subtitle>
        <slot
          name="item-subtitle"
          v-bind="{ result }"
        />
      </v-list-item-subtitle>
      <slot
        name="item-content"
        v-bind="{ result }"
      />
    </div>
    <template #append>
      <slot
        name="action-right"
        v-bind="{ result }"
      />
    </template>
  </v-list-item>
</template>