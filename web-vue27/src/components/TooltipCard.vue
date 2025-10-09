<script>
import { defineComponent } from 'vue';

export default defineComponent({
  props: {
    text: {
      type: String,
      required: true,
    },
  },
  setup() {
    return { id: `tooltipCard-${Math.random().toString().slice(2, 10)}` };
  },
});
</script>

<template>
  <v-card
    :id="id"
    outlined
  >
    <v-tooltip
      :attach="`#${id}`"
      left
      nudge-bottom="20px"
      min-width="300px"
      max-width="300px"
    >
      <template #activator="{ on, attrs }">
        <v-icon
          v-bind="attrs"
          style="position: absolute; right: 6px; top: 6px; z-index: 2;"
          v-on="on"
        >
          mdi-help-circle
        </v-icon>
      </template>
      <span v-html="text" />
    </v-tooltip>
    <slot />
  </v-card>
</template>
