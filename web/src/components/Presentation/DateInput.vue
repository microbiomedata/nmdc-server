<script>
import Vue from 'vue';
import moment from 'moment';
import * as chrono from 'chrono-node';

export default Vue.extend({
  props: {
    value: {
      type: String,
      required: true,
    },
  },

  data() {
    return {
      menu: false,
      textFieldRules: [(v) => chrono.parse(v).length === 1 || 'Invalid date'],
      textFieldDate: moment(this.value).format('MMM D, YYYY'),
    };
  },

  computed: {
    isoDate() {
      return moment(this.value).format('YYYY-MM-DD');
    },
  },

  methods: {
    updateFromTextField(event) {
      const parsed = chrono.parse(event);
      if (parsed.length === 1) {
        const parse = parsed[0];
        this.$emit('input', parse.date().toISOString());
      }
    },
    updateFromDatePicker(event) {
      const date = moment(event);
      this.textFieldDate = date.format('MMM D, YYYY');
      this.$emit('input', date.format('YYYY-MM-DDT00:00:00.000'));
    },
  },
});
</script>

<template>
  <v-menu
    ref="menu"
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
        @click="$refs.menu.save(value)"
      >
        OK
      </v-btn>
    </v-date-picker>
  </v-menu>
</template>
