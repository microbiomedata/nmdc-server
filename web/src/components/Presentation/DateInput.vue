<script>
import { defineComponent, ref, computed } from 'vue';
import moment from 'moment';
import * as chrono from 'chrono-node';

export default defineComponent({
  props: {
    modelValue: {
      type: String,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const menu = ref(false);
    const menuRef = ref(null);
    const textFieldDate = ref(moment(props.modelValue).format('MMM D, YYYY'));

    const textFieldRules = [
      (v) => chrono.parse(v).length === 1 || 'Invalid date',
    ];

    const isoDate = computed({
      get: () => moment(props.modelValue).format('YYYY-MM-DD'),
      set: (value) => {
        updateFromDatePicker(value);
      },
    });

    function updateFromTextField(event) {
      const parsed = chrono.parse(event);
      if (parsed.length === 1) {
        const parse = parsed[0];
        emit('update:modelValue', parse.date().toISOString());
      }
    }

    function updateFromDatePicker(event) {
      const date = moment(event);
      textFieldDate.value = date.format('MMM D, YYYY');
      emit('update:modelValue', date.format('YYYY-MM-DDT00:00:00.000'));
    }

    function closeMenu() {
      // if (menuRef.value) {
      //   menuRef.value.save(props.modelValue);
      // }
      menu.value = false;
    }

    return {
      menu,
      textFieldDate,
      textFieldRules,
      isoDate,
      menuRef,
      closeMenu,
      updateFromTextField,
      updateFromDatePicker,
    };
  },
});
</script>

<template>
  <v-menu
    ref="menuRef"
    v-model="menu"
    :close-on-content-click="false"
    :return-value="modelValue"
    transition="scale-transition"
    location="end"
    open-on-click
    min-width="290px"
  >
    <template #activator="{ props }">
      <v-text-field
        v-model="textFieldDate"
        :rules="textFieldRules"
        label="Choose"
        prepend-icon="mdi-calendar"
        v-bind="props"
        variant="underlined"
        @update:model-value="updateFromTextField"
      />
    </template>
    <v-card>
      <v-date-picker
        v-model="isoDate"
        elevation="0"
        no-title
        scrollable
        @update:model-value="updateFromDatePicker"
      />
      <div class="d-flex justify-end pa-2">
        <v-btn
          text
          variant="plain"
          color="primary"
          @click="closeMenu"
        >
          OK
        </v-btn>
      </div>
    </v-card>
  </v-menu>
</template>
