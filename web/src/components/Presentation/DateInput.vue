<script>
import Vue from 'vue';
import moment from 'moment';

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
    };
  },

  computed: {
    formattedDate() {
      return moment(this.value).format('MMM Do, YYYY');
    },
    isoDate() {
      return moment(this.value).format('YYYY-MM-DD');
    },
  },

  methods: {
    update(event) {
      this.$emit('input', moment(event).format('YYYY-MM-DDT00:00:00.000'));
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
    offset-y
    min-width="290px"
  >
    <template #activator="{ on, attrs }">
      <v-text-field
        :value="formattedDate"
        label="Choose"
        prepend-icon="mdi-calendar"
        readonly
        v-bind="attrs"
        v-on="on"
      />
    </template>
    <v-date-picker
      :value="isoDate"
      no-title
      scrollable
      @input="update"
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
