<script lang="ts">
import { BaseSearchResult } from '@/data/api';
import Vue, { PropType } from 'vue';

export default Vue.extend({
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
});
</script>

<template>
  <div>
    <v-pagination
      v-if="count > itemsPerPage && !disablePagination"
      :value="page"
      :length="Math.ceil(count / itemsPerPage)"
      :total-visible="7"
      @input="$emit('set-page', $event)"
    />
    <v-list>
      <template
        v-for="(result, resultIndex) in results"
      >
        <v-divider
          v-if="resultIndex > 0"
          :key="`${result.id}-divider`"
        />
        <v-list-item
          :key="result.id"
          v-on="{
            click: disableNavigateOnClick
              ? null /* will warn, but /shrug */
              : () => $emit('selected', result.id),
          }"
        >
          <slot
            name="action"
            v-bind="{ result }"
          />
          <v-list-item-avatar>
            <v-icon
              v-text="icon"
            />
          </v-list-item-avatar>
          <v-list-item-content>
            <v-list-item-title>
              {{ result.name }}
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ result.description || 'No description' }}
            </v-list-item-subtitle>
            <slot
              name="item-content"
              v-bind="{ result }"
            />
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-list>
  </div>
</template>
