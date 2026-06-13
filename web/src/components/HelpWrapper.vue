<script setup lang="ts">
const { text } = defineProps<{
  text: string;
}>();
</script>

<template>
  <v-sheet
    class="h-100"
  >
    <v-tooltip
      location="left"
      offset="20"
      min-width="300px"
      max-width="300px"
    >
      <template #activator="{ props }">
        <v-icon
          v-bind="props"
          color="grey-darken-1"
          style="position: absolute; right: 6px; top: 6px; z-index: 2;"
        >
          mdi-help-circle
        </v-icon>
      </template>
      <span v-html="text" />
    </v-tooltip>
    <slot />
  </v-sheet>
</template>
