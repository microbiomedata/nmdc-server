<script setup lang="ts">
import { ref } from 'vue';
import LabelValueTableRow from './LabelValueTableRow.vue';

export interface LabelValuePair {
  iconString?: string;
  label: string;
  value?: string | number | null;
  href?: string;
}

/**
 * Displays a flat list of metadata as label-value pairs.
 */
withDefaults(defineProps<{
  defaultRows?: LabelValuePair[];
  hiddenRows?: LabelValuePair[];
  iconWidth?: number;
  labelWidth?: number;
  togglerMoreAdjective?: string;
  togglerLessAdjective?: string;
  togglerNoun?: string;
}>(), {
  defaultRows: () => [],
  hiddenRows: () => [],
  iconWidth: 32,
  labelWidth: 200,
  togglerMoreAdjective: 'more',
  togglerLessAdjective: 'fewer',
  togglerNoun: 'items',
});

const showHiddenRows = ref(false);

function toggleHiddenRows() {
  showHiddenRows.value = !showHiddenRows.value;
}
</script>

<template>
  <v-table
    class="label-value-table"
    density="compact"
  >
    <tbody>
      <LabelValueTableRow
        v-for="(row, index) in defaultRows"
        :key="index"
        :row="row"
        :icon-width="iconWidth"
        :label-width="labelWidth"
      />
      <tr
        v-if="hiddenRows.length > 0"
        class="toggle-hidden-rows"
        @click="toggleHiddenRows"
      >
        <td
          :colspan="3"
          class="text-center"
        >
          <span>
            Show {{ showHiddenRows ? togglerLessAdjective : togglerMoreAdjective }} {{ togglerNoun }}
          </span>
          <v-icon
            size="small"
            class="mr-2"
          >
            {{ showHiddenRows ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
          </v-icon>
        </td>
      </tr>
      <template v-if="showHiddenRows">
        <LabelValueTableRow
          v-for="(row, index) in hiddenRows"
          :key="index"
          :row="row"
          :icon-width="iconWidth"
          :label-width="labelWidth"
        />
      </template>
    </tbody>
  </v-table>
</template>

<style scoped>
.label-value-table :deep(th),
.label-value-table :deep(td) {
  border-bottom: 0;
  padding-left: 0;
  user-select: text !important;
}

.icon-cell {
  box-sizing: border-box;
  padding-right: 8px !important;
}

.toggle-hidden-rows {
  cursor: pointer;
}
</style>
