<script lang="ts">
import {
  defineComponent,
  ref,
  computed,
  PropType,
} from 'vue';
import { Condition, opType } from '@/data/api';

import DateInput from './DateInput.vue';

export default defineComponent({
  components: { DateInput },

  props: {
    field: {
      type: String as PropType<string>,
      required: true,
    },
    type: {
      type: String as PropType<string>,
      required: true,
    },
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
    min: {
      type: String as PropType<string>,
      required: true,
    },
    max: {
      type: String as PropType<string>,
      required: true,
    },
    update: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['select'],
  setup(props, { emit }) {
    const options = [
      { text: 'is between', value: 'between' },
      { text: 'is greater than', value: '>' },
      { text: 'is greater than or equal to', value: '>=' },
      { text: 'is less than', value: '<' },
      { text: 'is less than or equal to', value: '<=' },
      { text: 'is equal to', value: '==' },
      { text: 'is not', value: '!=' },
    ];
    const selectedOption = ref<opType>('between');
    const value1 = ref(props.min.toString());
    const value2 = ref(props.max.toString());

    // conditions from OTHER fields
    const otherConditions = computed(() => props.conditions.filter((c) => (c.field !== props.field) || (c.table !== props.type)));

    // conditions that match our field.
    const myConditions = computed(() => props.conditions.filter((c) => (c.field === props.field) && (c.table === props.type)));

    // If we have an existing condition for this field, use it to set our initial state.
    if (myConditions.value.length === 1) {
      const [condition] = myConditions.value;
      selectedOption.value = condition?.op || 'between';
      if (condition?.op === 'between' && typeof condition.value === 'object') {
        const conditionValueStrings = condition.value.map((v) => v.toString());
        if (conditionValueStrings.length === 2 && conditionValueStrings[0] && conditionValueStrings[1]) {
          [value1.value, value2.value] = conditionValueStrings;
        } else {
          value1.value = props.min.toString();
          value2.value = props.max.toString();
        }
      } else {
        value1.value = condition?.value.toString() || props.min.toString();
      }
    }

    function addFilter() {
      const value = selectedOption.value === 'between'
        ? [value1.value, value2.value]
        : value1.value;
      const condition = {
        field: props.field,
        op: selectedOption.value,
        value,
        table: props.type,
      };
      emit('select', {
        conditions: [...otherConditions.value, condition],
      });
    }

    return {
      options,
      selectedOption,
      value1,
      value2,
      otherConditions,
      myConditions,
      addFilter,
    };
  },
});
</script>

<template>
  <div class="d-flex flex-column">
    <v-select
      v-model="selectedOption"
      :items="options"
      item-title="text"
      item-value="value"
      hide-details
      variant="outlined"
      flat
      density="compact"
      class="pb-4"
    />
    <div class="d-flex flex-row align-center pb-4">
      <DateInput v-model="value1" />
      <template v-if="selectedOption === 'between'">
        <span class="px-4">and</span>
        <DateInput v-model="value2" />
      </template>
    </div>
    <v-btn
      block
      color="primary"
      @click="addFilter"
    >
      {{ update ? 'Update' : 'Add' }} Filter
    </v-btn>
  </div>
</template>
