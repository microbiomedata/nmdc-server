<script>
import { bin, extent, ticks } from 'd3-array';
import { scaleBand, scaleLinear } from 'd3-scale';
import { timeDay } from 'd3-time';
import { timeFormat } from 'd3-time-format';

const canvas = document.createElement('canvas');
const context = canvas.getContext('2d');
const measureWidth = (text, size, face) => {
  context.font = `${size}px ${face}`;
  return context.measureText(text).width;
};

export default {
  props: {
    data: {
      type: Array, // Array<Object.valueOf>
      required: true,
    },
    binWidth: {
      type: Number, // in pixels
      default: 10,
    },
    width: {
      type: Number,
      required: true,
    },
    height: {
      type: Number,
      required: true,
    },
    range: {
      type: Array,
      default: () => ([0, 100]),
    },
  },

  data() {
    return {
      padding: 25,
    };
  },

  computed: {
    chartDimensions() {
      return {
        width: this.width - this.padding * 2,
        height: this.height - this.padding * 2,
        padding: this.padding,
      };
    },
    bands() {
      return scaleBand()
        .domain(this.binned.map((d, i) => i))
        .rangeRound([
          this.chartDimensions.padding,
          this.chartDimensions.width + this.chartDimensions.padding,
        ])
        .padding([0.2]);
    },
    bandwidth() {
      return this.bands.bandwidth();
    },
    bin() {
      return bin().thresholds(60).domain(this.scaledRange);
    },
    binned() {
      return this.bin(this.dataValues);
    },
    binnedDomain() {
      return this.binned.map((b) => ({
        height: this.y(b.length),
        key: b.x0,
      }));
    },
    dataValuesRaw() {
      return this.data.map((d) => d.valueOf());
    },
    dataValues() {
      const { scaledRange } = this;
      return this.dataValuesRaw.filter((d) => (d >= scaledRange[0] && d <= scaledRange[1]));
    },
    rangeScale() {
      const outerExtent = extent(this.dataValuesRaw);
      return scaleLinear()
        .domain([0, 100])
        .range(outerExtent);
    },
    scaledRange() {
      const scaleRange = this.rangeScale;
      const scaledMin = scaleRange(this.range[0]);
      const scaledMax = scaleRange(this.range[1]);
      return [scaledMin, scaledMax];
    },
    step() {
      return this.bands.step();
    },
    ticks() {
      return ticks(this.scaledRange[0], this.scaledRange[1], 6)
        .map((tick) => {
          const text = this.tickFormat(tick);
          const size = 12;
          const left = this.x(tick) - (measureWidth(text, size, 'sans') / 2);
          return {
            raw: tick,
            text,
            key: (new Date(tick)).toLocaleString('en-US'),
            left,
            style: {
              fontSize: `${size}px`,
              transform: `translate(${left}px)`,
            },
          };
        });
    },
    x() {
      return scaleLinear()
        .domain(this.scaledRange)
        .range([
          this.chartDimensions.padding,
          this.chartDimensions.width + this.chartDimensions.padding,
        ]);
    },
    y() {
      /* Find the tallest bar */
      const yextent = extent(this.binnedDomain);
      return scaleLinear()
        .domain([0, yextent[1]])
        .range([
          this.chartDimensions.padding,
          this.chartDimensions.height + this.chartDimensions.padding,
        ]);
    },
  },

  methods: {
    tickFormat(date) {
      const days = timeDay.count(...this.scaledRange);
      if (days < 120) {
        return timeFormat('%x')(date);
      }
      return timeFormat('%b %Y')(date);
    },
  },
};
</script>

<template>
  <g>
    <g class="histogram">
      <rect
        v-for="(bd, i) in binnedDomain"
        :key="bd.key"
        :x="bands(i)"
        :width="bands.bandwidth()"
        :y="height - bd.height"
        :height="bd.height - chartDimensions.padding"
        :fill="$vuetify.theme.currentTheme.accent"
      />
    </g>
    <g class="axis">
      <text
        v-for="(tick) in ticks"
        :key="tick.key"
        :y="height - 3"
        :style="tick.style"
      >
        {{ tick.text }}
      </text>
    </g>
  </g>
</template>

<style scoped>
.histogram rect {
  transition: all 0.2s;
}
.axis text {
  transition: all 0.2s;
}
</style>
