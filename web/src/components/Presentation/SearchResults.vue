<script lang="ts">
import { defineComponent, PropType, ref } from 'vue';

import { BaseSearchResult } from '@/data/api';

export default defineComponent({
  props: {
    page: {
      type: Number,
      required: true,
    },
    itemsPerPage: {
      type: Number,
      required: true,
    },
    count: {
      type: Number,
      required: true,
    },
    titleKey: {
      type: String,
      default: 'name',
    },
    subtitleKey: {
      type: String,
      default: 'description',
    },
    results: {
      type: Array as PropType<BaseSearchResult[]>,
      default: () => [],
    },
    icon: {
      type: String,
      default: 'mdi-book',
    },
    disableNavigateOnClick: {
      type: Boolean,
      default: false,
    },
    disablePagination: {
      type: Boolean,
      default: false,
    },
  },
  setup(props) {
    const rows = ref(props.itemsPerPage);
    return {
      rows,
    };
  },

});

</script>

<template>
  <div>
    <div
      v-if="!disablePagination"
      class="d-flex pt-2 pb-0 align-end justify-center"
    >
      <v-pagination
        :model-value="page"
        :length="Math.ceil(count / rows)"
        :total-visible="7"
        active-color="primary"
        @update:model-value="$emit('set-page', $event)"
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
        @update:model-value="$emit('set-items-per-page', $event)"
      />
    </div>
    <v-list
      density="compact"
      class="rounded-b"
    >
      <template
        v-for="(result, resultIndex) in results"
        :key="result.id"
      >
        <v-divider
          v-if="resultIndex > 0"
        />

        <v-list-item
          :ripple="!disableNavigateOnClick"
          :active="false"
          v-on="{
            click: disableNavigateOnClick
              ? () => {}
              : () => $emit('selected', result.id),
          }"
        >
          <template #prepend>
            <slot
              name="action"
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
              <slot
                name="child-list"
                v-bind="{ result}"
              />
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
    </v-list>
  </div>
</template>