<script setup lang="ts">
export interface LabelValuePair {
  iconString?: string;
  label: string;
  value?: string | number | null;
}

/**
 * Displays a flat list of metadata as label-value pairs.
 */
withDefaults(defineProps<{
  rows?: LabelValuePair[];
  iconWidth?: number;
  labelWidth?: number;
}>(), {
  rows: () => [],
  iconWidth: 32,
  labelWidth: 200,
});
</script>

<template>
  <v-table
    class="label-value-table"
    density="compact"
  >
    <tbody>
      <tr
        v-for="(row, index) in rows"
        :key="index"
      >
        <td
          class="icon-cell"
          :style="{
            width: `${iconWidth}px`,
            minWidth: `${iconWidth}px`,
            maxWidth: `${iconWidth}px`,
          }"
        >
          <v-icon
            v-if="row.iconString"
            size="small"
          >
            {{ row.iconString }}
          </v-icon>
        </td>
        <th
          class="label-cell text-medium-emphasis"
          scope="row"
          :style="{
            width: `${labelWidth}px`,
            minWidth: `${labelWidth}px`,
            maxWidth: `${labelWidth}px`,
          }"
        >
          <slot
            name="label"
            :row="row"
            :index="index"
          >
            {{ row.label }}
          </slot>
        </th>
        <td class="value-cell">
          <slot
            name="value"
            :row="row"
            :index="index"
          >
            {{ row.value || '-' }}
          </slot>
        </td>
      </tr>
    </tbody>
  </v-table>
</template>

<style scoped>
.label-value-table :deep(th),
.label-value-table :deep(td) {
  border-bottom: 0;
  padding-left: 0;
}

.icon-cell {
  box-sizing: border-box;
  padding-right: 8px !important;
}
</style>
