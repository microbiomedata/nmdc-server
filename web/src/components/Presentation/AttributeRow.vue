<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  props: {
    label: {
      type: String,
      required: false,
      default: '',
    },
    hint: {
      type: String,
      required: false,
      default: '',
    },
  },
  setup() {
    return {};
  },
});
</script>

<template>
  <v-row
    dense
    class="mb-2"
  >
    <v-col
      cols="12"
      md="2"
    >
      <template v-if="$slots.label">
        <slot name="label" />
      </template>
      <div
        v-else
        class="font-weight-medium"
      >
        {{ label }}
        <div
          v-if="hint"
          class="text--secondary text-caption"
        >
          {{ hint }}
        </div>
      </div>
    </v-col>
    <v-col
      cols="12"
      md="10"
    >
      <slot />
    </v-col>
  </v-row>
</template>
