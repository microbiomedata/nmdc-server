<template>
  <div>
    <v-pagination
      v-if="Math.ceil(results.length / resultsPerPage) > 1"
      v-model="page"
      :length="Math.ceil(results.length / resultsPerPage)"
      :total-visible="7"
    />
    <v-list
      two-line
      class="pa-0"
    >
      <template
        v-for="(result, resultIndex) in results.slice(resultsPerPage*(page-1), resultsPerPage*page)"
      >
        <v-divider
          v-if="resultIndex > 0"
          :key="`${result.id}-divider`"
        />
        <v-list-item
          :key="result.id"
          @click="$emit('selected', {
            type: type,
            conditions: [{ field: 'id', op: '==', value: result.id }]})"
        >
          <v-list-item-avatar>
            <v-icon
              v-text="types[type].icon"
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
<script>
import { types } from '../encoding';

export default {
  props: {
    type: {
      type: String,
      default: null,
    },
    results: {
      type: Array,
      default: () => [],
    },
    conditions: {
      type: Array,
      default: () => [],
    },
  },
  data: () => ({
    page: 1,
    resultsPerPage: 15,
    types,
  }),
};
</script>
