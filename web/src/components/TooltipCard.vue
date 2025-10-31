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
    class="h-100"
    :id="id"
    variant="outlined"
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
  </v-card>
</template>
