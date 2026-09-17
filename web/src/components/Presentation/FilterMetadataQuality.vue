<script setup lang="ts">
import { computed } from 'vue';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';

import type { Condition } from '@/data/api';
import { snakeToSentenceCase } from '@/utils';

type BadgeChoice = 'has' | 'lacks' | 'any';
type BadgeKey = keyof typeof NmdcSchema.enums.MetadataBadgeEnum.permissible_values;

const props = defineProps<{
  conditions: Condition[];
}>();

const emit = defineEmits<{
  (e: 'select', value: { conditions: Condition[] }): void;
}>();

const badges = Object.keys(
  NmdcSchema.enums.MetadataBadgeEnum.permissible_values,
) as BadgeKey[];

const badgeConditions = computed(() => props.conditions.filter(
  (condition) => condition.table === 'biosample'
    && condition.field === 'badges'
    && (condition.op === 'has' || condition.op === 'lacks'),
));

function selectedChoice(badge: BadgeKey): BadgeChoice {
  const condition = badgeConditions.value.find((candidate) => candidate.value === badge);
  if (condition?.op === 'has' || condition?.op === 'lacks') {
    return condition.op;
  }
  return 'any';
}

function selectChoice(badge: BadgeKey, choice: BadgeChoice | null): void {
  if (!choice) {
    return;
  }

  const otherConditions = props.conditions.filter((condition) => !(
    condition.table === 'biosample'
      && condition.field === 'badges'
      && condition.value === badge
  ));

  const conditions = choice === 'any'
    ? otherConditions
    : [
      ...otherConditions,
      {
        table: 'biosample',
        field: 'badges',
        op: choice,
        value: badge,
      } satisfies Condition,
    ];

  emit('select', { conditions });
}
</script>

<template>
  <div>
    <v-card-text class="py-1 text-caption">
      Each biosample can earn metadata quality badges representing different categories of metadata.
    </v-card-text>
    <v-table density="compact">
      <thead>
        <tr>
          <th scope="col">
            Badge
          </th>
          <th
            v-for="heading in ['Yes', 'No', 'Any']"
            :key="heading"
            scope="col"
            class="text-center"
          >
            {{ heading }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="badge in badges"
          :key="badge"
        >
          <th
            scope="row"
            class="font-weight-regular"
          >
            {{ snakeToSentenceCase(badge) }}
          </th>
          <td
            v-for="choice in (['has', 'lacks', 'any'] as const)"
            :key="choice"
          >
            <v-radio
              :model-value="selectedChoice(badge) === choice"
              :name="`metadata-quality-${badge}`"
              :aria-label="`${snakeToSentenceCase(badge)} ${choice === 'has' ? 'Yes' : choice === 'lacks' ? 'No' : 'Any'}`"
              class="badge-option"
              color="primary"
              density="compact"
              @click="selectChoice(badge, choice)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

<style scoped>
th:first-child {
  width: 58%;
}

th:not(:first-child) {
  width: 14%;
}

.badge-option {
  justify-content: center;
}
</style>
