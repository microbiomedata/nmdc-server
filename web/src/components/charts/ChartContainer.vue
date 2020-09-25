<script>
/*
  ChartContainer provides information like width and height to a chart.
  It might be reasonable to provide this in the future with composition functions.
*/
export default {
  props: {
    width: {
      type: Number,
      default: 1000,
    },
    height: {
      type: Number,
      default: 100,
    },
  },
  computed: {
    widths() {
      return `${this.width}px`;
    },
    heights() {
      return `${this.height}px`;
    },
  },
};
</script>

<template>
  <div :style="{ width: widths, height: heights }">
    <svg
      ref="svg"
      :width="widths"
      :height="heights"
    >
      <slot v-bind="{ width, height }" />
    </svg>
    <div>
      <slot name="below" />
    </div>
  </div>
</template>
