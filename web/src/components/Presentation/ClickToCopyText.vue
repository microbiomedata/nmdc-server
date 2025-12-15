<script lang="ts">
import { defineComponent, ref } from 'vue';

/**
 * ClickToCopyText provides a container that copies its text content to the clipboard when clicked.
 */
export default defineComponent({
  setup() {
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

    return {
      containerRef,
      handleClick,
      isTooltipVisible,
    };
  },
});
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
            <span
              v-bind="hoverProps"
              ref="containerRef"
              class="slot-container"
              @click="handleClick"
            >
              <slot />
              <v-icon
                v-if="isHovering"
                class="ml-1"
                size="inherit"
              >
                mdi-content-copy
              </v-icon>
            </span>
          </template>
        </v-hover>
      </span>
    </template>

    <span>Copied</span>
  </v-tooltip>
</template>

<style scoped>
.slot-container {
  cursor: pointer;
}
</style>
