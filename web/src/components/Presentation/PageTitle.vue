<script lang="ts">
import { defineComponent, type PropType } from 'vue';

export default defineComponent({
  props: {
    title: {
      type: [String, Array] as PropType<string | string[]>,
      required: true,
    },
    subtitle: {
      type: String,
      required: false,
      default: '',
    },
    help: {
        type: String,
        required: false,
        default: '',
    }
  },
  setup() {
    return {};
  },
});
</script>

<template>
  <div class="mb-8">
    <div class="d-flex">
      <div class="text-h4 mb-2">
        {{ title }}
      </div>

      <div class="text-body-1">
        <div v-if="help || $slots.help">
          <slot name="help" />
          {{ help }}
        </div>
      </div>
    </div>

    <div class="text-body-1">
      <div v-if="subtitle || $slots.subtitle">
        <slot name="subtitle" />
        {{ subtitle }}
      </div>
    </div>
  </div>
</template>
