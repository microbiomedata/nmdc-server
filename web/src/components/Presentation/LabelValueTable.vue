<script setup lang="ts">
import { ref } from 'vue';
import LabelValueTableRow from './LabelValueTableRow.vue';

export interface LabelValuePair {
  /** Vuetify material icon string (e.g. 'mdn-test-tube') to show next to the label */
  iconString?: string;
  /** String to show in the left label column */
  label: string;
  /** Value to show in the right value column */
  value?: string | number | null;
  /** Optional URL to link to when the value is clicked */
  href?: string;
}

/**
 * Displays a flat list of metadata as label-value pairs.
 */
withDefaults(defineProps<{
  /** Array of label-value pairs that will always be visible in the table */
  alwaysVisibleRows?: LabelValuePair[];
  /** Array of label-value pairs that can be toggled visible (hidden by default) */
  hideableRows?: LabelValuePair[];
  /** Width of the left icon column in pixels */
  iconWidth?: number;
  /** Width of the left label column in pixels */
  labelWidth?: number;
  /** Text to show when clicking to expand hideable rows */
  expandButtonText?: string;
  /** Text to show when clicking to collapse hideable rows */
  collapseButtonText?: string;
}>(), {
  alwaysVisibleRows: () => [],
  hideableRows: () => [],
  iconWidth: 32,
  labelWidth: 200,
  expandButtonText: 'Show more',
  collapseButtonText: 'Show fewer',
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
        v-for="(row, index) in alwaysVisibleRows"
        :key="index"
        :row="row"
        :icon-width="iconWidth"
        :label-width="labelWidth"
      />
      <tr
        v-if="hideableRows.length > 0"
        class="toggle-hidden-rows"
        @click="toggleHiddenRows"
      >
        <td
          :colspan="3"
          class="text-center"
        >
          <span>
            {{ showHiddenRows ? collapseButtonText : expandButtonText }}
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
          v-for="(row, index) in hideableRows"
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
