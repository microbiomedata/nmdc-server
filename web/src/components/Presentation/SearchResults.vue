<script setup lang="ts">
import { ref } from 'vue';

import { BiosampleSearchResult, StudySearchResult } from '@/data/api';

interface Props {
  page: number;
  itemsPerPage: number;
  count: number;
  titleKey?: string;
  results?: StudySearchResult[] | BiosampleSearchResult[];
  icon?: string;
  disablePagination?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  titleKey: 'name',
  results: () => [] as StudySearchResult[] | BiosampleSearchResult[],
  icon: 'mdi-book-outline',
  disablePagination: false,
});

const emit = defineEmits<{
  'set-page': [page: number];
  'set-items-per-page': [itemsPerPage: number];
}>();

const rows = ref(props.itemsPerPage);
</script>

<template>
  <div>
    <v-list>
      <template
        v-for="(result, resultIndex) in results"
        :key="result.id"
      >
        <v-divider
          v-if="resultIndex > 0"
        />
        <SearchResultItem
          v-bind="{
            result,
            titleKey,
            icon,
          }"
        >
          <template
            v-if="$slots['action-left']"
            #action-left="slotProps"
          >
            <slot
              name="action-left"
              v-bind="slotProps"
            />
          </template>
          <template
            v-if="$slots['item-title']"
            #item-title="slotProps"
          >
            <slot
              name="item-title"
              v-bind="slotProps"
            />
          </template>
          <template
            v-if="$slots['item-subtitle']"
            #item-subtitle="slotProps"
          >
            <slot
              name="item-subtitle"
              v-bind="slotProps"
            />
          </template>
          <template
            v-if="$slots['item-content']"
            #item-content="slotProps"
          >
            <slot
              name="item-content"
              v-bind="slotProps"
            />
          </template>
          <template
            v-if="$slots['action-right']"
            #action-right="slotProps"
          >
            <slot
              name="action-right"
              v-bind="slotProps"
            />
          </template>
        </SearchResultItem>
        <slot
          name="item-children"
          v-bind="{ result }"
        />
      </template>
    </v-list>
    <div
      v-if="!disablePagination && count > 0"
      class="d-flex pt-2 pb-0 align-end justify-center"
    >
      <v-pagination
        :model-value="page"
        :length="Math.ceil(count / rows)"
        :total-visible="7"
        active-color="primary"
        @update:model-value="emit('set-page', $event)"
      />
      <!-- flex-basis is based on the "Items per page" label. Since it is absolutely
           positioned it doesn't count towards the `auto` width -->
      <v-select
        v-model="rows"
        :items="[5, 10, 15, 20]"
        label="Items per page"
        class="ml-4 mb-1 flex-grow-0"
        :style="{ 'flex-basis': '6rem' }"
        hide-details
        variant="plain"
        @update:model-value="emit('set-items-per-page', $event)"
      />
    </div>
  </div>
</template>
