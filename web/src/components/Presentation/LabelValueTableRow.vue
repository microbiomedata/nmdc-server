<script setup lang="ts">
import { LabelValuePair } from '@/components/Presentation/LabelValueTable.vue';

/**
 * Displays and formats a row inside a LabelValueTable.
 */
withDefaults(defineProps<{
  row: LabelValuePair;
  iconWidth?: number;
  labelWidth?: number;
}>(), {
  iconWidth: 32,
  labelWidth: 200,
});
</script>

<template>
  <tr>
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
      >
        {{ row.label }}
      </slot>
    </th>
    <td class="value-cell">
      <slot
        name="value"
        :row="row"
      >
        <a
          v-if="row.href"
          :href="row.href"
        >
          {{ row.value || '-' }}
        </a>
        <span v-else>{{ row.value || '-' }}</span>
      </slot>
    </td>
  </tr>
</template>