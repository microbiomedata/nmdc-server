<script setup lang="ts">
import moment from 'moment';
import {
  ref,
  computed,
  watch,
  nextTick,
} from 'vue';

import ChartContainer from '@/components/Presentation/ChartContainer.vue';
import TimeHistogram from '@/components/Presentation/TimeHistogram.vue';
import { BinResponse, Condition } from '@/data/api';

const props = withDefaults(defineProps<{
  facetSummary: BinResponse<string> | null;
  facetSummaryUnconditional: BinResponse<string> | null;
  otherConditions: Condition[];
  myConditions: Condition[];
  table: string;
  field: string;
  height?: number;
  errorMessage: string | null;
}>(), {
  height: 160,
});

const emit = defineEmits<{
  (e: 'select', payload: { type: string; conditions: Condition[] }): void;
}>();

const range = ref<[number, number] | null>(null);
const min = ref(0);
const max = ref(100);

function onBrushEnd(brushRange: [number, number] | null) {
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
        } as Condition,
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
    const minDate = Date.parse(props.facetSummaryUnconditional.bins[0]!);
    const maxDate = Date.parse(
      props.facetSummaryUnconditional.bins[props.facetSummaryUnconditional.bins.length - 1]!,
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
    if (condition && condition.op === 'between' && typeof condition.value === 'object') {
      // If range is already set, figure it out from the condition.
      nextTickCallBack = () => {
        // but get min/max from full range anyway.
        setMinMax();
        range.value = (condition.value as string[]).map((c) => (new Date(c)).valueOf()) as [number, number];
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
console.log(props.errorMessage);
const isLoading = computed(() => !props.errorMessage
  && (!props.facetSummary
  || !props.facetSummaryUnconditional
  || !props.facetSummaryUnconditional.bins
  || props.facetSummaryUnconditional.bins.length === 0));
</script>

<template>
  <div class="histogram">
    <div
      v-if="isLoading || props.errorMessage"
      class="d-flex justify-center align-center"
      :style="{ height: `${height}px` }"
    >
      <v-progress-circular
        v-if="isLoading"
        indeterminate
        color="primary"
      />
      <div v-else>
        {{ props.errorMessage }}
      </div>
    </div>
    <ChartContainer
      v-else
      :height="height"
    >
      <template #default="{ width }">
        <TimeHistogram
          ref="histogram"
          v-bind="{ width, height, selectedData: facetSummary, totalData: facetSummaryUnconditional, range: range || [] }"
          @on-brush-end="onBrushEnd"
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
