<script lang='ts'>
import {
  computed, defineComponent, reactive, onMounted, ref, watch, toRef,
} from '@vue/composition-api';
import { brushX, D3BrushEvent } from 'd3-brush';
import { scaleLinear } from 'd3-scale';
import { select as d3select } from 'd3-selection';

interface IProps {
  value: number[];
  width: number;
  height: number;
  min: number;
  max: number;
  fmt(d: number): string;
  round(d: number): number;
}

export default defineComponent<IProps>({
  props: ['value', 'width', 'height', 'min', 'max', 'fmt', 'round'],
  setup(props, { emit, root }) {
    let changed = false;
    const data = reactive({
      lazyValue: props.value,
      margin: {
        top: 2,
        bottom: 14,
        left: 64,
        right: 64,
      },
    });
    const round = props.round || ((d: number) => d);
    const internalValue = computed({
      get: () => data.lazyValue,
      set: (val: number[]) => {
        if (val.some((d, i) => round(d) !== round(data.lazyValue[i]))) {
          data.lazyValue = val.map(round);
          changed = true;
          emit('input', val);
        }
      },
    });
    const svgRef = ref(undefined as (SVGElement | undefined));
    const width = computed(() => props.width - data.margin.left - data.margin.right);
    const height = computed(() => props.height - data.margin.top - data.margin.bottom);
    const xScale = computed(() => scaleLinear()
      .domain([props.min, props.max])
      .range([0, width.value]));
    const brushResizePath = computed(() => {
      const h = height.value;
      return (d: any) => {
        const e = +(d.type === 'e');
        const x = e ? 1 : -1;
        const y = h * (0.8);
        // eslint-disable-next-line prefer-template
        return 'M' + (0.5 * x) + ',' + y + 'A6,6 0 0 ' + e + ' ' + (6.5 * x) + ','
          + (y + 6) + 'V' + (2 * y - 6) + 'A6,6 0 0 ' + e + ' ' + (0.5 * x)
          + ',' + (2 * y) + 'ZM' + (2.5 * x) + ',' + (y + 8) + 'V' + (2 * y - 8)
          + 'M' + (4.5 * x) + ',' + (y + 8) + 'V' + (2 * y - 8);
      };
    });

    /**
     * Construct the DOM elements in-memory once
     */
    const g = d3select(document.createElementNS('http://www.w3.org/2000/svg', 'g'));
    const labelL = g.append('text')
      .attr('id', 'labelleft')
      .attr('x', 0);
    const labelR = g.append('text')
      .attr('id', 'labelright')
      .attr('x', 0);
    const gBrush = g.append('g')
      .attr('class', 'brush');
    const handle = gBrush.selectAll('.handle--custom')
      .data([{ type: 'w' }, { type: 'e' }])
      .enter().append('path')
      .attr('class', 'handle--custom')
      .attr('stroke', '#000')
      .attr('fill', '#bbb')
      .attr('cursor', 'ew-resize');
    const brush = brushX()
      .extent([[0, 0], [width.value, height.value]])
      .on('brush', (event: D3BrushEvent<number>) => {
        const s = event.selection as number[];
        // update and move labels
        labelL.attr('x', s[0])
          .text(props.fmt(xScale.value.invert(s[0])));
        labelR.attr('x', s[1])
          .text(props.fmt(xScale.value.invert(s[1])));
        // move brush handles
        handle.attr(
          'transform',
          (d, i) => `translate(${s[i]}, ${-height.value * 0.68})`,
        );
        internalValue.value = s.map(xScale.value.invert);
      }).on('end', () => {
        if (changed) {
          emit('end');
        }
        changed = false;
      });
    gBrush.call(brush);
    g.selectAll('.selection')
      .attr('fill', root.$vuetify.theme.currentTheme.accent as string);
    /**
     * Any attributes from reactive properties should be set in
     * this update function.
     */
    function update(w: number, h: number, min: number, max: number, value: number[]) {
      xScale.value.range([0, width.value]);
      xScale.value.domain([props.min, props.max]);
      labelL.attr('y', h + 5);
      labelR.attr('y', h + 5);
      g.attr('transform', `translate(${data.margin.left}, ${data.margin.top})`);
      handle.attr('d', brushResizePath.value);
      brush.extent([[0, 0], [w, h]]);
      gBrush.call(brush);
      gBrush.call(brush.move, value.map(xScale.value));
    }

    /**
     * Insert the newly created DOM on mount
     */
    onMounted(() => {
      if (svgRef.value === undefined) throw new Error('SVG was undefined');
      const node = g.node();
      if (node !== null) {
        svgRef.value.appendChild(node);
      }
      update(width.value, height.value, props.min, props.max, internalValue.value);
    });

    /**
     * Redraw the input range on external update,
     * but prevent it from being emitted back up.
     */
    watch([
      width,
      height,
      toRef(props, 'min'),
      toRef(props, 'max'),
      internalValue,
    ], () => {
      update(width.value, height.value, props.min, props.max, internalValue.value);
    });

    watch(toRef(props, 'value'), () => {
      internalValue.value = props.value;
    });

    return { svgRef };
  },
});
</script>

<template>
  <svg
    id="rangeslider"
    ref="svgRef"
    :width="width"
    :height="height"
  />
</template>

<style lang="scss">
#rangeslider {
  svg {
    font-family: sans-serif;
  }

  rect.overlay {
    fill: black;
    fill-opacity: 0.14;
  }

  rect.selection {
    stroke: none;
    fill-opacity: 0.5;
  }

  #labelleft,
  #labelright {
    dominant-baseline: hanging;
    font-size: 12px;
  }

  #labelleft {
    text-anchor: end;
  }

  #labelright {
    text-anchor: start;
  }
}
</style>
