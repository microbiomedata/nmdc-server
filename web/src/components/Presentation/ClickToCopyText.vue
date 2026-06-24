<script setup lang="ts">
import { ref } from 'vue';

/**
 * ClickToCopyText provides a container that copies its text content to the clipboard when clicked.
 */
const { iconOverlay } = defineProps<{
  /** If true, the copy icon will be overlaid on the right edge of the text instead of appearing to the right of it. */
  iconOverlay?: boolean;
}>();
const isTooltipVisible = ref(false);
const containerRef = ref<HTMLElement | null>(null);

const handleClick = () => {
  const text = containerRef.value?.innerText || '';
  navigator.clipboard.writeText(text.trim());
  isTooltipVisible.value = true;
  setTimeout(() => {
    isTooltipVisible.value = false;
  }, 2000);
};
</script>

<template>
  <v-tooltip
    v-model="isTooltipVisible"
    :open-on-hover="false"
    location="top"
  >
    <template #activator="{ props: tooltipProps }">
      <span v-bind="tooltipProps">
        <v-hover>
          <template #default="{ isHovering, props: hoverProps }">
            <!-- Intentionally using <button> here instead of <v-btn> because it should be completely unstyled
                 (i.e. look like plain text) but still have the accessibility features of a native button. -->
            <button
              v-bind="hoverProps"
              ref="containerRef"
              class="slot-container position-relative"
              @click="handleClick"
            >
              <slot />
              <v-icon
                v-if="isHovering"
                class="ml-1 position-absolute"
                :style="{
                  backgroundColor: '#ffffff',
                  top: '50%',
                  right: iconOverlay ? 0 : '-20px',
                  transform: 'translateY(-50%)',
                  zIndex: 100
                }"
                size="inherit"
              >
                mdi-content-copy
              </v-icon>
            </button>
          </template>
        </v-hover>
      </span>
    </template>

    <span>Copied</span>
  </v-tooltip>
</template>

<style scoped>
.slot-container {
  letter-spacing: inherit;
}
</style>
