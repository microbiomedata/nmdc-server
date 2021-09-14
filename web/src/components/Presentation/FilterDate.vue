<script lang="ts">
import Vue, { PropType } from 'vue';
import { Condition, opType } from '@/data/api';

import DateInput from './DateInput.vue';

interface Options {
  text: string;
  value: opType;
}

export default Vue.extend({
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

  data() {
    return {
      options: [
        { text: 'is between', value: 'between' },
        { text: 'is greater than', value: '>' },
        { text: 'is greater than or equal to', value: '>=' },
        { text: 'is less than', value: '<' },
        { text: 'is less than or equal to', value: '<=' },
        { text: 'is equal to', value: '==' },
        { text: 'is not', value: '!=' },
      ],
      selectedOption: 'between' as opType,
      value1: this.min.toString(),
      value2: this.max.toString(),
    };
  },

  computed: {
    otherConditions(): Condition[] {
      // conditions from OTHER fields
      return this.conditions.filter((c) => (c.field !== this.field) || (c.table !== this.type));
    },
    myConditions(): Condition[] {
      // conditions that match our field.
      return this.conditions.filter((c) => (c.field === this.field) && (c.table === this.type));
    },
  },

  created() {
    this.loadFromConditions();
  },

  methods: {
    loadFromConditions() {
      if (this.myConditions.length === 1) {
        const [condition] = this.myConditions;
        this.selectedOption = condition.op;
        if (condition.op === 'between' && typeof condition.value === 'object') {
          [this.value1, this.value2] = condition.value.map((v) => v.toString());
        } else {
          this.value1 = condition.value.toString();
        }
      }
    },
    addFilter() {
      const value = this.selectedOption === 'between'
        ? [this.value1, this.value2]
        : this.value1;
      const condition = {
        field: this.field,
        op: this.selectedOption,
        value,
        table: this.type,
      };
      this.$emit('select', {
        conditions: [...this.otherConditions, condition],
      });
    },
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
