<script lang="ts">
import Vue from 'vue';

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
export default Vue.extend({
  props: {
    height: {
      type: Number,
      default: 120,
    },
  },
  data() {
    return {
      width: 800,
      ro: null,
    };
  },
  computed: {
    widths(): string {
      return `${this.width}px`;
    },
    heights(): string {
      return `${this.height}px`;
    },
  },
  mounted() {
    // TODO: https://github.com/Microsoft/TypeScript/issues/28502
    // @ts-ignore
    this.ro = (new ResizeObserver((entries: ResizeObserverEntry[]) => {
      entries.forEach((entry) => {
        this.width = entry.contentRect.width;
      });
    })).observe(this.$refs.container);
  },
});
</script>

<template>
  <div ref="container">
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
