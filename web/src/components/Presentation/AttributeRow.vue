<script lang="ts">
import { defineComponent } from 'vue';

/**
 * AttributeRow is a second-level organization unit for detail pages. It
 * provides a label (with optional hint) and a slot for content.
 *
 * See also: PageSection.vue for a first-level organization unit.
 */
export default defineComponent({
  props: {
    /**
     * Optional label for the attribute row. If a 'label' slot is provided, it
     * will take precedence over this prop. If neither is provided, no label
     * will be displayed.
     */
    label: {
      type: String,
      required: false,
      default: '',
    },
    /**
     * Optional hint text to provide additional context for the label.
     */
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
