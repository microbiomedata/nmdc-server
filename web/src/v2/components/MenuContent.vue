<script lang="ts">
import Vue, { PropType } from 'vue';
import { fieldDisplayName } from '@/util';
import { getField } from '@/encoding';

import FilterDate from '@/components/Presentation/FilterDate.vue';
import FilterFloat from '@/components/Presentation/FilterFloat.vue';
import FilterList from '@/components/Presentation/FilterList.vue';
import FilterTree from '@/components/Presentation/FilterTree.vue';
import FilterStringLiteral from '@/v2/components/FilterStringLiteral.vue';
import { AttributeSummary, Condition, entityType } from '@/data/api';

export default Vue.extend({
  components: {
    FilterDate,
    FilterFloat,
    FilterList,
    FilterStringLiteral,
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
    table: {
      type: String as PropType<entityType>,
      required: true,
    },
    summary: {
      type: Object as PropType<AttributeSummary>,
      required: true,
    },
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },

  methods: { fieldDisplayName, getField },
});
</script>

<template>
  <div>
    <v-card-title class="pb-0">
      {{ fieldDisplayName(field, table) }} {{ getField(field, table).units }}
    </v-card-title>
    <filter-list
      v-if="summary.type === 'string' && isOpen"
      :field="field"
      :table="table"
      :conditions="conditions"
      @select="$emit('select', $event)"
    />
    <filter-string-literal
      v-if="summary.type === 'string_literal' && isOpen"
      :field="field"
      :table="table"
      :conditions="conditions"
      @select="$emit('select', $event)"
    />
    <filter-date
      v-if="summary.type === 'date'"
      v-bind="{
        field, type: table, conditions,
        min: summary.min,
        max: summary.max,
      }"
      class="pa-5"
      @select="$emit('select', $event)"
    />
    <filter-float
      v-else-if="['float', 'integer'].includes(summary.type)"
      v-bind="{
        field, type: table, conditions,
        min: summary.min,
        max: summary.max,
      }"
      class="pa-5"
      @select="$emit('select', $event)"
    />
    <filter-tree
      v-else-if="['tree'].includes(summary.type) && isOpen"
      v-bind="{ field, table, conditions }"
      @select="$emit('select', $event)"
    />
  </div>
</template>
