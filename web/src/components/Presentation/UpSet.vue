<script>
import { defineComponent, watchEffect, ref } from '@vue/composition-api';
import { select } from 'd3-selection';
import { scaleBand, scaleLinear } from 'd3-scale';
import { MultiomicsValue } from '@/encoding';

export default defineComponent({
  props: {
    data: {
      type: Array,
      required: true,
    },
    tooltips: {
      type: Object,
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

  setup(props, { root, emit }) {
    const svgRoot = ref(undefined);

    const margin = {
      top: 26,
      right: 30,
      bottom: 10,
      left: 30,
    };
    const fontSize = 12;

    const setOrder = ['MG', 'MT', 'MP', 'MB', 'NOM', 'LIP', 'AMP'];
    const Samples = 'Samples';
    const Studies = 'Studies';
    const seriesTitles = [Samples, Studies];
    const uniqueCounts = [Samples];

    function makeUpSet(dataOrig, order, el) {
      const width = props.width - margin.left - margin.right;
      const height = props.height - margin.top - margin.bottom;

      const data = [...dataOrig]
        .sort((a, b) => b.counts[order] - a.counts[order])
        .filter((a) => a.counts[order] > 0);

      const uniqueSets = Array.from(
        new Set([].concat(...data.map((d) => d.sets))),
      ).sort((a, b) => setOrder.indexOf(a) - setOrder.indexOf(b));

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

      const selectSamples = (event, values) => {
        const value = values.sets.reduce((prev, cur) => {
          const next = prev | MultiomicsValue[cur]; //eslint-disable-line no-bitwise
          return next;
        }, 0);
        const conditions = [{
          field: 'multiomics',
          table: 'biosample',
          op: 'has',
          value,
        }];
        emit('select', { conditions });
      };

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
        .attr('font-size', fontSize)
        .text((d) => d)
        .attr('fill', 'black')
        .append('svg:title')
        .text((s) => props.tooltips[s]);

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

      uniqueCounts.forEach((count, _i) => {
        const barX = scaleLinear()
          .domain([0, Math.max(...data.map((d) => d.counts[count]))])
          .range([0, countsX.bandwidth()]);

        svg.append('g')
          .call((parent) => {
            parent.append('text')
              .attr('x', countsX(count))
              .attr('y', -4)
              .attr('font-size', fontSize)
              .attr('fill', 'black')
              .text(seriesTitles[_i]);
          })
          .selectAll('rect')
          .data(data)
          .enter()
          .call((parent) => {
            parent.append('rect')
              .attr('x', countsX(count))
              .attr('y', (d, i) => y(i))
              .attr('width', (d) => barX(d.counts[count]))
              .attr('height', y.bandwidth())
              .attr('fill', root.$vuetify.theme.currentTheme.blue)
              .classed('upset-bar-clickable', true)
              .on('click', selectSamples);
            parent.append('text')
              .attr('class', 'count')
              .attr('class', 'upset-bar-clickable')
              .attr('x', (d) => countsX(count) + barX(d.counts[count]) + 3)
              .attr('y', (d, i) => y(i) + (y.bandwidth() / 2) + 4)
              .attr('font-size', fontSize)
              .text((d) => d.counts[count])
              .attr('fill', 'black')
              .on('click', selectSamples);
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

<style>
.upset-bar-clickable {
  cursor: pointer;
}
.upset-bar-clickable:hover {
  fill: rgba(0, 0, 0, .5) !important;
}
</style>
