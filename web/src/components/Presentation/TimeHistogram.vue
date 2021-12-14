<script>
import { defineComponent, watchEffect, ref } from '@vue/composition-api';
import { select } from 'd3-selection';
import { max } from 'd3-array';
import { axisBottom } from 'd3-axis';
import { scaleLinear, scaleTime } from 'd3-scale';

/**
 * Time Histogram lifted from
 * https://bl.ocks.org/d3noob/96b74d0bd6d11427dd797892551a103c
 */
export default defineComponent({
  props: {
    data: {
      type: Object, // Array<Object.valueOf>
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
      required: true,
    },
  },

  setup(props, { root }) {
    const svgRoot = ref(undefined);
    // set the dimensions and margins of the graph
    const margin = {
      top: 20,
      right: 30,
      bottom: 30,
      left: 30,
    };

    function makeHistogram(data, el) {
      const width = props.width - margin.left - margin.right;
      const height = props.height - margin.top - margin.bottom;

      /**
       * Forge bins from this.data
       * [ { x0: min, x1: max, length: count }, { ... } ]
       */
      const bins = [];
      data.facets.forEach((count, i) => {
        bins.push({
          length: count,
          x0: Date.parse(data.bins[i]),
          x1: Date.parse(data.bins[i + 1]),
        });
      });

      if (bins.length === 0) {
        return;
      }

      // set the ranges
      const x = scaleTime()
        .domain(props.range)
        .rangeRound([0, width]);
      const y = scaleLinear().range([height, 0]);

      // Reset the SVG
      select(el).selectAll('g').remove();

      // append the svg object to the body of the page
      // append a 'group' element to 'svg'
      // moves the 'group' element to the top left margin
      const svg = select(el)
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', 'translate('.concat(margin.left, ',', margin.top, ')'));

      // Scale the range of the data in the y domain
      y.domain([
        0,
        max(bins, (d) => d.length),
      ]);

      // append the bar rectangles to the svg element
      const enterSelection = svg
        .selectAll('rect')
        .data(bins)
        .enter();
      enterSelection.append('rect')
        .attr('class', 'bar')
        .attr('x', 1)
        .attr('fill', root.$vuetify.theme.currentTheme.primary)
        .attr('transform', (d) => 'translate('.concat(x(d.x0), ',', y(d.length), ')'))
        .attr('width', (d) => {
          const w = x(d.x1) - x(d.x0);
          const padding = w * 0.1;
          return w - padding;
        })
        .attr('height', (d) => ((d.length > 0) ? (height - y(d.length) + 1) : 0));

      const domain = x.domain();
      const millisecondsPerYear = 3.154 * (10 ** 10);
      if (domain[1] - domain[0] < (millisecondsPerYear * 4)) {
        enterSelection
          .filter((d) => d.length > 0)
          .append('text')
          .attr('x', 1)
          .attr('transform', (d) => `translate(${x(d.x0)}, ${y(d.length) - 4})`)
          .attr('font-size', '10px')
          .html((d) => d.length);
      }

      // add the x Axis
      svg
        .append('g')
        .attr('transform', 'translate(0,'.concat(height + 10, ')'))
        .call(axisBottom(x));

      svg.select('path').remove();

      // add the y Axis
      // svg.append('g').call(axisLeft(y));
    }

    watchEffect(() => {
      const { data } = props;
      const el = svgRoot.value;
      if (data.bins && data.facets) {
        makeHistogram(data, el);
      }
    });

    return { svgRoot };
  },
});
</script>

<template>
  <svg ref="svgRoot" />
</template>

<style scoped>
.bar {
  color: purple;
}

.histogram rect {
  transition: all 0.2s;
}
</style>
