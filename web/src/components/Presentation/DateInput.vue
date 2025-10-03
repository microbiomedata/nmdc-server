<script>
import { defineComponent, ref, computed } from 'vue';
import moment from 'moment';
import * as chrono from 'chrono-node';

export default defineComponent({
  props: {
    value: {
      type: String,
      required: true,
    },
  },

  setup(props, { emit }) {
    const menu = ref(false);
    const menuRef = ref(null);
    const textFieldDate = ref(moment(props.value).format('MMM D, YYYY'));

    const textFieldRules = [
      (v) => chrono.parse(v).length === 1 || 'Invalid date',
    ];

    const isoDate = computed(() => moment(props.value).format('YYYY-MM-DD'));

    function updateFromTextField(event) {
      const parsed = chrono.parse(event);
      if (parsed.length === 1) {
        const parse = parsed[0];
        emit('input', parse.date().toISOString());
      }
    }

    function updateFromDatePicker(event) {
      const date = moment(event);
      textFieldDate.value = date.format('MMM D, YYYY');
      emit('input', date.format('YYYY-MM-DDT00:00:00.000'));
    }

    function closeMenu() {
      if (menuRef.value) {
        menuRef.value.save(props.value);
      }
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
    :return-value="value"
    transition="scale-transition"
    offset-x
    offset-y
    min-width="290px"
  >
    <template #activator="{ on, attrs }">
      <v-text-field
        v-model="textFieldDate"
        :rules="textFieldRules"
        label="Choose"
        prepend-icon="mdi-calendar"
        v-bind="attrs"
        v-on="on"
        @input="updateFromTextField"
      />
    </template>
    <v-date-picker
      :value="isoDate"
      no-title
      scrollable
      @input="updateFromDatePicker"
    >
      <v-spacer />
      <v-btn
        text
        color="primary"
        @click="closeMenu"
      >
        OK
      </v-btn>
    </v-date-picker>
  </v-menu>
</template>
