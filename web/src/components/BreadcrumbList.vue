<script lang="ts" setup>
import { RouteLocationRaw } from 'vue-router';

export interface BreadcrumbListItem {
  text: string;
  to?: RouteLocationRaw;
  copyable?: boolean;
}

defineProps<{
  /**
   * The list of breadcrumb items to display.
   * Each item can have:
   * - text: The display text for the breadcrumb item.
   * - to: (optional) The route location to link to. If provided, the item will be a link.
   * - copyable: (optional) If true and 'to' is not provided, the item will be rendered as copyable text.
   */
  items: BreadcrumbListItem[];
}>();
</script>

<template>
  <div class="text-caption mb-3">
    <template
      v-for="(item, index) in items"
      :key="index"
    >
      <span
        v-if="index > 0"
        class="mx-2"
      >/</span>
      <router-link
        v-if="item.to"
        :to="item.to"
      >
        {{ item.text }}
      </router-link>
      <ClickToCopyText
        v-else-if="item.copyable"
      >
        {{ item.text }}
      </ClickToCopyText>
      <span v-else>
        {{ item.text }}
      </span>
    </template>
  </div>
</template>
