<script>
import { fieldDisplayName } from '@/util';
import FloatFilter from '@/components/Presentation/FloatFilter.vue';

import MatchList from './MatchList.vue';

export default {
  components: {
    FloatFilter,
    MatchList,
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
};
</script>

<template>
  <div>
    <v-card-title class="pb-0">
      {{ fieldDisplayName(field) }}
    </v-card-title>
    <MatchList
      v-if="['string', 'date'].includes(summary.type) && isOpen"
      :field="field"
      :type="type"
    />
    <FloatFilter
      v-else-if="['float', 'integer'].includes(summary.type)"
      v-bind="{
        field, type, conditions,
        min: summary.min,
        max: summary.max,
      }"
      class="pa-5"
      @select="$store.dispatch('route', $event)"
    />
  </div>
</template>
