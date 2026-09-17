<script setup lang="ts">
import { computed } from 'vue';
import { snakeToSentenceCase } from '@/utils';
import biogeochemistryIcon from '@/assets/biogeochemistry.png';
import expertCurationIcon from '@/assets/expert_curation.png';
import hostInformationIcon from '@/assets/host_information.png';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';

export type BadgeKey = keyof typeof NmdcSchema.enums.MetadataBadgeEnum.permissible_values;

const badgeIcons: Record<BadgeKey, string> = {
  biogeochemistry: biogeochemistryIcon,
  expert_curation: expertCurationIcon,
  host_information: hostInformationIcon,
};

const props = defineProps<{
  /** Badge string identifier as defined in the schema (e.g. 'expert_curation') */
  badge: BadgeKey;
}>();

const badgeSchema = computed(
  () => NmdcSchema.enums.MetadataBadgeEnum.permissible_values[props.badge],
);
const badgeIcon = computed(() => badgeIcons[props.badge]);

if (!badgeSchema.value) {
  console.warn(`Unknown badge: ${props.badge}`);
}
</script>

<template>
  <v-tooltip
    v-if="badgeSchema"
    :text="badgeSchema.description"
    location="bottom"
    max-width="400px"
  >
    <template #activator="{ props: tooltipProps }">
      <a
        v-if="badgeSchema"
        v-bind="tooltipProps"
        class="metadata-badge"
        :href="badgeSchema.see_also[0] || '#'"
        target="_blank"
        rel="noopener noreferrer"
      >
        <div class="badge-circle">
          <v-img
            :src="badgeIcon"
            :alt="badgeSchema.description"
            width="64"
            height="64"
            contain
          />
        </div>
        <div class="badge-label">{{ snakeToSentenceCase(badge) }}</div>
      </a>
    </template>
  </v-tooltip>
</template>

<style scoped>
.metadata-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.metadata-badge:hover {
  text-decoration: none !important;
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
