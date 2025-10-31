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

    console.log(menu.value);

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
        @update:modelValue="updateFromTextField"
      />
    </template>
    <v-date-picker
      v-model="isoDate"
      no-title
      scrollable
      @update:modelValue="updateFromDatePicker"
    />
    <v-btn
      text
      color="primary"
      @click="closeMenu"
    >
      OK
    </v-btn>
  </v-menu>
</template>
