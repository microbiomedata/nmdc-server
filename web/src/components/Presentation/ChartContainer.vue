<script lang="ts">
import {
  computed, defineComponent, onBeforeUnmount, onMounted, ref,
} from 'vue';

interface ResizeObserverEntry {
  contentRect: Readonly<{
    width: number;
    height: number;
  }>;
  target: Readonly<Element | SVGElement>;
}
/*
  ChartContainer provides information like width and height to a chart.
  It might be reasonable to provide this in the future with composition functions.
*/
export default defineComponent({
  props: {
    height: {
      type: Number,
      default: 120,
    },
  },

  setup(props) {
    const width = ref(800);
    const widths = computed(() => `${width.value}px`);
    const heights = computed(() => `${props.height}px`);
    const containerRef = ref();
    const ro = new ResizeObserver((entries: ResizeObserverEntry[]) => {
      entries.forEach((entry) => {
        width.value = entry.contentRect.width || 200;
      });
    });

    onMounted(() => {
      if (containerRef.value) {
        ro.observe(containerRef.value);
      }
    });
    onBeforeUnmount(() => {
      ro?.disconnect();
    });

    return {
      width,
      widths,
      heights,
      containerRef,
    };
  },
});
</script>

<template>
  <div ref="containerRef">
    <div :style="{ width: widths, height: heights }">
      <svg
        ref="svg"
        :width="widths"
        :height="heights"
      >
        <slot v-bind="{ width, height }" />
      </svg>
    </div>
    <slot
      name="below"
      v-bind="{ width }"
    />
  </div>
</template>
