<script>
import { defineComponent, watchEffect, ref } from '@vue/composition-api';
import { select } from 'd3-selection';
import { scaleBand, scaleLinear } from 'd3-scale';

export default defineComponent({
  props: {
    data: {
      type: Array,
      required: true,
    },
    order: {
      type: String,
      required: true,
    },
    width: {
      type: Number,
      required: true,
    },
    height: {
      type: Number,
      required: true,
    },
  },

  setup(props, { root }) {
    const svgRoot = ref(undefined);

    const margin = {
      top: 20,
      right: 30,
      bottom: 30,
      left: 30,
    };

    function makeUpSet(dataOrig, order, el) {
      const width = props.width - margin.left - margin.right;
      const height = props.height - margin.top - margin.bottom;

      const data = [...dataOrig].sort((a, b) => b.counts[order] - a.counts[order]);

      const uniqueSets = Array.from(
        new Set([].concat(...data.map((d) => d.sets))),
      ).sort();
      const uniqueCounts = Array.from(
        new Set([].concat(...data.map((d) => Object.keys(d.counts)))),
      );
      const setMembers = [].concat(
        ...data.map((d, i) => d.sets.map((s) => ({ index: i, set: s }))),
      );

      const membershipWidth = 0.5 * width;

      const membershipX = scaleBand()
        .domain(uniqueSets)
        .range([0, membershipWidth]);
      const y = scaleBand()
        .domain(data.map((d, i) => i))
        .range([0, height])
        .paddingInner(0.2);
      const countsX = scaleBand()
        .domain(uniqueCounts)
        .range([membershipWidth, width])
        .paddingInner(0.2);

      select(el).selectAll('g').remove();

      const svg = select(el)
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

      svg.selectAll('line.set')
        .data(uniqueSets)
        .enter()
        .append('line')
        .attr('class', 'set')
        .attr('x1', (s) => membershipX(s))
        .attr('x2', (s) => membershipX(s))
        .attr('y1', 0)
        .attr('y2', height)
        .attr('stroke', 'black');

      svg.selectAll('text.set')
        .data(uniqueSets)
        .enter()
        .append('text')
        .attr('class', 'set')
        .attr('x', (s) => membershipX(s))
        .attr('y', -4)
        .attr('text-anchor', 'middle')
        .attr('font-size', margin.top - 8)
        .text((d) => d)
        .attr('fill', 'black');

      svg.selectAll('line.membership')
        .data(data)
        .enter()
        .append('line')
        .attr('class', 'membership')
        .attr('x1', (d) => Math.min(...d.sets.map((s) => membershipX(s))))
        .attr('x2', (d) => Math.max(...d.sets.map((s) => membershipX(s))))
        .attr('y1', (d, i) => y(i) + y.step() / 2)
        .attr('y2', (d, i) => y(i) + y.step() / 2)
        .attr('stroke-width', 3)
        .attr('stroke', root.$vuetify.theme.currentTheme.blue);

      svg.selectAll('circle')
        .data(setMembers)
        .enter().append('circle')
        .attr('cx', (d) => membershipX(d.set))
        .attr('cy', (d) => y(d.index) + y.step() / 2)
        .attr('r', 5)
        .attr('fill', root.$vuetify.theme.currentTheme.blue);

      uniqueCounts.forEach((count) => {
        const barX = scaleLinear()
          .domain([0, Math.max(...data.map((d) => d.counts[count]))])
          .range([0, countsX.bandwidth()]);

        svg.append('g')
          .selectAll('rect')
          .data(data)
          .enter()
          .call((parent) => {
            parent.append('rect')
              .attr('x', countsX(count))
              .attr('y', (d, i) => y(i))
              .attr('width', (d) => barX(d.counts[count]))
              .attr('height', y.bandwidth())
              .attr('fill', root.$vuetify.theme.currentTheme.blue);
            parent.append('text')
              .attr('class', 'count')
              .attr('x', (d) => countsX(count) + barX(d.counts[count]) + 3)
              .attr('y', (d, i) => y(i) + 12)
              .attr('font-size', margin.top - 8)
              .text((d) => d.counts[count])
              .attr('fill', 'black');
          });
      });
    }

    watchEffect(() => {
      const { data, order } = props;
      const el = svgRoot.value;
      makeUpSet(data, order, el);
    });

    return { svgRoot };
  },
});
</script>

<template>
  <svg ref="svgRoot" />
</template>
