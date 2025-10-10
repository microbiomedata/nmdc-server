<script lang="ts">
import {
  defineComponent,
  PropType,
  ref,
  computed,
} from 'vue';
import { Condition, opType } from '@/data/api';

export default defineComponent({
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
      type: Number as PropType<number>,
      required: true,
    },
    max: {
      type: Number as PropType<number>,
      required: true,
    },
    update: {
      type: Boolean,
      default: false,
    },
  },

  setup(props, { emit }) {
    const options = ref([
      { text: 'is between', value: 'between' },
      { text: 'is greater than', value: '>' },
      { text: 'is greater than or equal to', value: '>=' },
      { text: 'is less than', value: '<' },
      { text: 'is less than or equal to', value: '<=' },
      { text: 'is equal to', value: '==' },
      { text: 'is not', value: '!=' },
    ]);
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
      selectedOption.value = condition.op;
      if (condition.op === 'between' && typeof condition.value === 'object') {
        [value1.value, value2.value] = condition.value.map((v) => v.toString());
      } else {
        value1.value = condition.value.toString();
      }
    }

    function addFilter() {
      const value = selectedOption.value === 'between'
        ? [parseFloat(value1.value), parseFloat(value2.value)]
        : parseFloat(value1.value);
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
      hide-details
      outlined
      flat
      dense
      class="pb-4"
    />
    <div class="d-flex flex-row align-center pb-4">
      <v-text-field
        v-model="value1"
        type="number"
        required
        hide-details
        dense
        flat
        outlined
      />
      <template v-if="selectedOption === 'between'">
        <span class="px-4">and</span>
        <v-text-field
          v-model="value2"
          type="number"
          required
          hide-details
          dense
          flat
          outlined
        />
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
