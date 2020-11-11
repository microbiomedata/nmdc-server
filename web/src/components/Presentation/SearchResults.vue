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
  },
});
</script>

<template>
  <div>
    <v-pagination
      v-if="count > itemsPerPage"
      :value="page"
      :length="Math.ceil(count / itemsPerPage)"
      :total-visible="7"
      class="py-2 pt-3"
      @input="$emit('set-page', $event)"
    />
    <v-list
      two-line
      class="pa-0"
    >
      <template
        v-for="(result, resultIndex) in results"
      >
        <v-divider
          v-if="resultIndex > 0"
          :key="`${result.id}-divider`"
        />
        <v-list-item
          :key="result.id"
          @click="$emit('selected', result.id)"
        >
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
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-list>
  </div>
</template>
