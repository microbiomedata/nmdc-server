<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  props: {
    heading: {
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
  <div class="mb-16">
    <div
      v-if="heading || $slots.heading"
      class="text-h5 mb-4"
    >
      <template v-if="heading">
        {{ heading }}
      </template>
      <template v-else>
        <slot name="heading" />
      </template>
    </div>
    <slot>
      <i class="text-medium-emphasis">
        No information available
      </i>
    </slot>
  </div>
</template>
