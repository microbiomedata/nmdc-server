<script lang="ts">
import { defineComponent } from 'vue';

/**
 * PageSection is a first-level organization unit for detail pages. It
 * provides an optional heading and a slot for content. If no content is
 * provided, a fallback message is displayed.
 *
 * See also: AttributeRow.vue for a second-level organization unit within
 *    a PageSection.
 */
export default defineComponent({
  props: {
    /**
     * Optional heading for the section. If not provided, the 'heading' slot
     * will be used instead. If neither is provided, no heading will be
     * displayed.
     */
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
