<script lang="ts">
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  props: {
    href: {
      type: String,
      required: true,
    },
  },
});
</script>

<template>
  <v-card>
    <v-card-title>Terms and Conditions</v-card-title>
    <v-card-text>
      Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
      incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
      exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute
      irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
      nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa
      qui officia deserunt mollit anim id est laborum.
    </v-card-text>
    <v-divider />
    <v-card-actions>
      <v-spacer />
      <v-btn
        color="primary"
        text
        :href="href"
        target="_blank"
        rel="noopener"
        @click="$emit('clicked')"
      >
        Accept and continue to download
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
