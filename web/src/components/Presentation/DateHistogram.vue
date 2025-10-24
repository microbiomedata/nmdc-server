<script>
import moment from 'moment';
import {
  defineComponent,
  ref,
  watch,
  nextTick,
} from 'vue';

import ChartContainer from '@/components/Presentation/ChartContainer.vue';
import TimeHistogram from '@/components/Presentation/TimeHistogram.vue';

export default defineComponent({
  name: 'DateHistogram',
  components: {
    ChartContainer,
    TimeHistogram,
  },
  props: {
    facetSummary: {
      type: Object,
      required: true,
    },
    facetSummaryUnconditional: {
      type: Object,
      required: true,
    },
    otherConditions: {
      type: Array,
      required: true,
    },
    myConditions: {
      type: Array,
      required: true,
    },
    table: {
      type: String,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    height: {
      type: Number,
      default: 160,
    },
  },

  setup(props, { emit }) {
    console.log('DateHistogram props:', props.facetSummaryUnconditional);
    const range = ref(null);
    const min = ref(0);
    const max = ref(100);

    function afterDrag() {
      if (range.value[0] !== min.value || range.value[1] !== max.value) {
        emit('select', {
          type: props.table,
          conditions: [
            ...props.otherConditions,
            {
              field: props.field,
              op: 'between',
              value: range.value.map((d) => moment(d).format('YYYY-MM-DDT00:00:00.000')),
              table: props.table,
            },
          ],
        });
      } else if (props.myConditions.length) {
        emit('select', {
          type: props.table,
          conditions: props.otherConditions,
        });
      }
    }
    function onBrushEnd(brushRange) {
      if (brushRange && (brushRange[0] !== min.value || brushRange[1] !== max.value)) {
        emit('select', {
          type: props.table,
          conditions: [
            ...props.otherConditions,
            {
              field: props.field,
              op: 'between',
              value: brushRange.map((d) => moment(d).format('YYYY-MM-DDT00:00:00.000')),
              table: props.table,
            },
          ],
        });
      } else if (props.myConditions.length) {
        emit('select', {
          type: props.table,
          conditions: props.otherConditions,
        });
      }
    }

    watch(() => props.facetSummary, () => {
      // Derive min/max from full range
      const setMinMax = () => {
        if (!props.facetSummaryUnconditional
        || !props.facetSummaryUnconditional.bins
        || props.facetSummaryUnconditional.bins.length === 0) {
          return;
        }
        const minDate = Date.parse(props.facetSummaryUnconditional.bins[0]);
        const maxDate = Date.parse(
          props.facetSummaryUnconditional.bins[props.facetSummaryUnconditional.bins.length - 1],
        );
        if (Number.isNaN(minDate) || Number.isNaN(maxDate)) {
          return;
        }
        min.value = minDate;
        max.value = maxDate;
        range.value = [min.value, max.value];
      };
      let nextTickCallBack = setMinMax;
      if (props.myConditions.length === 1) {
        const [condition] = props.myConditions;
        if (condition.op === 'between' && typeof condition.value === 'object') {
          // If range is already set, figure it out from the condition.
          nextTickCallBack = () => {
          // but get min/max from full range anyway.
            setMinMax();
            range.value = condition.value.map((c) => (new Date(c)).valueOf());
          };
        }
      }
      nextTick(() => nextTickCallBack());
    }, { immediate: true });
    watch(() => props.myConditions, () => {
      if (props.myConditions.length === 0) {
        // Otherwise, reset to min/max
        range.value = [min.value, max.value];
      }
    }, { immediate: true });

    return {
      range,
      afterDrag,
      onBrushEnd,
    };
  },
});
</script>

<template>
  <div class="histogram">
    <ChartContainer :height="height">
      <template #default="{ width }">
        <TimeHistogram
          ref="histogram"
          v-bind="{ width, height, selectedData: facetSummary, totalData: facetSummaryUnconditional, range: range || [] }"
          @onBrushEnd="onBrushEnd"
        />
      </template>
      <template #below>
        <div class="mx-4 d-flex">
          <v-spacer />
          <h4>Collection Date</h4>
          <v-spacer />
        </div>
      </template>
    </ChartContainer>
  </div>
</template>

<style scoped>
.histogram {
  width: 100%;
}
</style>
