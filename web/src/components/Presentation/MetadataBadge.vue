<script setup lang="ts">
import { snakeToSentenceCase } from '@/utils';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';

export type BadgeKey = keyof typeof NmdcSchema.enums.MetadataBadgeEnum.permissible_values;

const props = defineProps<{
  badge: BadgeKey;
}>();

const badgeSchema = NmdcSchema.enums.MetadataBadgeEnum.permissible_values[props.badge];

if (!badgeSchema) {
  console.warn(`Unknown badge: ${props.badge}`);
}
</script>

<template>
  <div
    v-if="NmdcSchema.enums.MetadataBadgeEnum.permissible_values[badge]"
    class="metadata-badge"
  >
    <div class="badge-circle">
      <v-img
        :src="`/src/assets/${badge}.png`"
        :alt="badgeSchema.description"
        width="64"
        height="64"
        contain
      />
    </div>
    <label class="badge-label">{{ snakeToSentenceCase(badge) }}</label>
  </div>
</template>

<style scoped>
.metadata-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.badge-circle {
  width: 5rem;
  height: 5rem;
  background-color: #fff;
  border: 4px solid rgb(var(--v-theme-accent));
  border-radius: 50%;
  padding: 0.5rem;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-label {
  background-color: rgb(var(--v-theme-accent));
  border-radius: 1rem;
  color: #000;
  margin-top: -1rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  z-index: 2;
}
</style>