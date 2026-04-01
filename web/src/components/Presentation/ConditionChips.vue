<script setup lang="ts">
import moment from 'moment';
import { ref, computed } from 'vue';
import { groupBy } from 'lodash';
import { EntityType, opMap, type Condition, type DatabaseSummaryResponse, type opType } from '@/data/api';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import { makeSetsFromBitmask } from '@/encoding';

const props = defineProps<{
  conditions: Condition[];
  dbSummary: DatabaseSummaryResponse;
}>();

defineEmits<{
  (e: 'remove', cond: Condition): void;
}>();

const menuState = ref<Record<string, boolean>>({});

const conditionGroups = computed(() => Object.entries(groupBy(
  props.conditions,
  (c) => JSON.stringify({ field: c.field, table: c.table }),
)).map(([group, conditions]) => {
  const parsed: { field: string; table: string } = JSON.parse(group);
  return {
    key: parsed.field + parsed.table,
    field: parsed.field,
    table: parsed.table as EntityType,
    conditions,
  };
}).sort((a, b) => a.key.localeCompare(b.key)));

function verb(op?: opType) {
  if (op) {
    return opMap[op];
  }
  return;
}

function valueTransform(val: unknown, field: string, type: string): string {
  // Special handling for multiomics
  if (field === 'multiomics' && type === 'biosample') {
    return Array.from(makeSetsFromBitmask(val as string)).join(', ');
  }
  // If it's not primitive
  if (val && typeof val === 'object') {
    const inner = (val as unknown[]).map((v) => valueTransform(v, field, type)).join(', ');
    return `(${inner})`;
  }
  const summary = ((props.dbSummary[type as keyof DatabaseSummaryResponse] || {}).attributes || {})[field];
  if (summary) {
    if (['float', 'integer', 'string', 'gene_search'].includes(summary.type)) {
      return fieldDisplayName(val);
    }
    if (['date'].includes(summary.type)) {
      return moment(val as string).format('MM/DD/YYYY');
    }
    if (['tree', 'sankey-tree'].includes(summary.type)) {
      return val as string;
    }
    throw new Error(`Unknown entity type for ${type}: ${field}: ${summary.type}`);
  }
  return val as string;
}

function toggleMenu(category: string, value: boolean): void {
  menuState.value[category] = value;
}
</script>

<template>
  <div>
    <transition-group name="list">
      <v-card
        v-for="group in conditionGroups"
        :key="group.key"
        class="d-flex flex-row pa-1 my-2"
        color="rgb(79, 59, 128, 0.2)"
      >
        <div style="width: 94%">
          <span class="text-subtitle-2">
            {{ fieldDisplayName(group.field, group.table) }}
          </span>
          <span class="text-caption">
            [{{ verb(group.conditions[0]?.op) }}]
          </span>
          <transition-group name="chip">
            <v-chip
              v-for="cond in group.conditions"
              :key="JSON.stringify(cond.value)"
              size="small"
              closable
              label
              class="ma-1 chip"
              style="max-width: 90%;"
              @click:close="$emit('remove', cond)"
            >
              <span class="chip-content">
                {{ valueTransform(cond.value, cond.field, cond.table) }}
              </span>
            </v-chip>
          </transition-group>
        </div>
        <v-menu
          v-if="group.key !== 'multiomicsbiosample' && group.table !== 'full_text_search'"
          v-model="menuState[group.key]"
          offset-x
          :nudge-right="10"
          :close-on-content-click="false"
        >
          <template #activator="{ props: activatorProps }">
            <div
              class="expand d-flex flex-column justify-center"
              style="width: 6%"
              v-bind="activatorProps"
            >
              <v-icon size="x-small">
                mdi-play
              </v-icon>
            </div>
          </template>
          <v-card
            width="500"
          >
            <slot
              name="menu"
              v-bind="{
                field: group.field,
                table: group.table,
                isOpen: menuState[group.key] ?? false,
                toggleMenu: (val: boolean) => toggleMenu(group.key, val),
              }"
            />
          </v-card>
        </v-menu>
      </v-card>
    </transition-group>
  </div>
</template>

<style scoped>
.expand {
  border-left: 1px solid grey;
  border-radius: 0 !important;
  cursor: pointer;
}
.chip {
  border: 2px solid;
}
.chip-content {
  max-width: 200px;
  overflow: hidden;
}

/* Transition styles for list */
.list-enter-active, .list-leave-active {
  transition: all 0.2s;
}
.list-leave-active {
  position: absolute;
}
.list-enter {
  opacity: 0;
  transform: translateX(100px);
}
.list-leave-to {
  opacity: 0;
  transform: translateX(-100px);
}
.list-move {
  transition: transform 0.2s;
}

/* Transition styles for chip */
.chip-enter-active  {
  transition: all 0.2s;
}
.chip-leave-active {
  position: absolute;
}
.chip-enter {
  opacity: 0;
  transform: translateX(100px);
}
.chip-leave-to {
  opacity: 0;
  transform: translateX(-50px);
}
.chip-move {
  transition: transform 0.2s;
}
</style>
