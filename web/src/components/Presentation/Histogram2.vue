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
      default: () => [0, 100],
    },
  },

  setup(props) {
    const root = ref(undefined);

    function makeHistogram(data, el) {
      // set the dimensions and margins of the graph
      const margin = {
        top: 10,
        right: 30,
        bottom: 30,
        left: 30,
      };
      const width = props.width - margin.left - margin.right;
      const height = props.height - margin.top - margin.bottom;

      // parse the date / time
      // const parseDate = timeParse('%d-%m-%Y');

      // set the ranges
      const x = scaleTime()
        .domain([new Date(2012, 1, 1), new Date(2019, 0, 1)])
        .rangeRound([0, width]);
      const y = scaleLinear().range([height, 0]);

      // append the svg object to the body of the page
      // append a 'group' element to 'svg'
      // moves the 'group' element to the top left margin
      const svg = select(el)
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', 'translate('.concat(margin.left, ',', margin.top, ')'));

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

      // Scale the range of the data in the y domain
      y.domain([
        0,
        max(bins, (d) => d.length),
      ]);

      // append the bar rectangles to the svg element
      svg
        .selectAll('rect')
        .data(bins)
        .enter()
        .append('rect')
        .attr('class', 'bar')
        .attr('x', 1)
        .attr('transform', (d) => 'translate('.concat(x(d.x0), ',', y(d.length), ')'))
        .attr('width', (d) => x(d.x1) - x(d.x0) - 3)
        .attr('height', (d) => ((d.length > 0) ? (height - y(d.length) + 1) : 0));

      // console.log(x(bins[0].))
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
      console.log('her2e');
      const { data } = props;
      const el = root.value;
      if (data.bins && data.facets) {
        makeHistogram(data, el);
      }
    });

    return { root };
  },
});
</script>

<template>
  <svg ref="root" />
</template>

<style scoped>
.histogram rect {
  transition: all 0.2s;
}
</style>
