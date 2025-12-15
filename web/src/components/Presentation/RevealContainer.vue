<script lang="ts">
import {
  computed,
  defineComponent,
  onMounted,
  onUnmounted,
  ref,
} from 'vue';

/**
 * RevealContainer provides a container that can reveal or hide overflowing content.
 */
export default defineComponent({
  props: {
    /**
     * Label for the toggle button when content is hidden
     * @default 'Show more'
     */
    showLabel: {
      type: String,
      default: 'Show more',
    },
    /**
     * Label for the toggle button when all content is shown
     * @default 'Show less'
     */
    hideLabel: {
      type: String,
      default: 'Show less',
    },
    /**
     * Maximum height of the container (in pixels) when content is hidden
     * @default 200
     */
    closedHeight: {
      type: Number,
      default: 200,
    },
    /**
     * Amount of content height (in pixels) beyond the closedHeight before showing the toggle button
     * @default 50
     */
    thresholdHeight: {
      type: Number,
      default: 50,
    },
  },
  setup(props) {
    const containerRef = ref<HTMLElement | null>(null);
    const contentRef = ref<HTMLElement | null>(null);
    const contentHeight = ref(props.closedHeight);

    const canCollapse = computed(() => (
      contentHeight.value > (props.closedHeight + props.thresholdHeight)
    ));
    const isCollapsed = ref(true);

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        contentHeight.value = entry.contentRect.height;
      }
    });

    onMounted(() => {
      if (contentRef.value) {
        observer.observe(contentRef.value);
      }
    });

    onUnmounted(() => {
      observer.disconnect();
    });

    function toggle() {
      isCollapsed.value = !isCollapsed.value;
    }

    return {
      containerRef,
      contentHeight,
      contentRef,
      isCollapsed,
      canCollapse,
      toggle,
    };
  },
});
</script>

<template>
  <div>
    <div
      ref="containerRef"
      :class="{
        'reveal-container': true,
        collapsed: canCollapse && isCollapsed,
      }"
      :style="{
        maxHeight: (canCollapse && isCollapsed) ? `${closedHeight}px` : `${contentHeight}px`
      }"
    >
      <div ref="contentRef">
        <slot />
      </div>
    </div>
    <div class="text-center">
      <v-btn
        v-if="canCollapse"
        variant="plain"
        :ripple="false"
        size="small"
        @click="toggle"
      >
        {{ isCollapsed ? showLabel : hideLabel }}
      </v-btn>
    </div>
  </div>
</template>

<style scoped>
.reveal-container {
  overflow: hidden;
  transition-property: max-height, box-shadow;
  transition-duration: 0.2s;
  transition-timing-function: ease-in-out;
}
.reveal-container.collapsed {
  box-shadow: inset 0 -20px 16px -25px rgba(0, 0, 0, 0.5);
}
</style>
