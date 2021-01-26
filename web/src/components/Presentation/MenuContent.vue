<script>
import Vue from 'vue';
import { fieldDisplayName } from '@/util';
import FilterDate from '@/components/Presentation/FilterDate.vue';
import FilterFloat from '@/components/Presentation/FilterFloat.vue';
import FilterList from '@/components/Presentation/FilterList.vue';
import FilterTree from '@/components/Presentation/FilterTree.vue';

export default Vue.extend({
  components: {
    FilterDate,
    FilterFloat,
    FilterList,
    FilterTree,
  },

  props: {
    isOpen: {
      type: Boolean,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    type: {
      // api.entityType
      type: String,
      required: true,
    },
    summary: {
      // api.AttributeSummary
      type: Object,
      required: true,
    },
    conditions: {
      // api.Condition[]
      type: Array,
      required: true,
    },
  },

  methods: { fieldDisplayName },
});
</script>

<template>
  <div>
    <v-card-title class="pb-0">
      {{ fieldDisplayName(field) }}
    </v-card-title>
    <filter-list
      v-if="['string'].includes(summary.type) && isOpen"
      :field="field"
      :table="type"
      @select="$emit('select', $event)"
    />
    <filter-date
      v-if="['date'].includes(summary.type)"
      v-bind="{
        field, type, conditions,
        min: summary.min,
        max: summary.max,
      }"
      class="pa-5"
      @select="$emit('select', $event)"
    />
    <filter-float
      v-else-if="['float', 'integer'].includes(summary.type)"
      v-bind="{
        field, type, conditions,
        min: summary.min,
        max: summary.max,
      }"
      class="pa-5"
      @select="$emit('select', $event)"
    />
    <filter-tree
      v-else-if="['tree'].includes(summary.type) && isOpen"
      v-bind="{ field, table: type, conditions }"
      @select="$emit('select', $event)"
    />
  </div>
</template>
