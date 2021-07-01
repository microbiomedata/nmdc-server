<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';

export default defineComponent({
  props: {
    href: {
      type: Object as PropType<string | undefined>,
      default: undefined,
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
});
</script>

<template>
  <v-card>
    <v-card-title>Terms and Conditions</v-card-title>
    <v-card-text>
      <div class="mb-3">
        These data are made available under the
        <a href="https://creativecommons.org/licenses/by/4.0/">
          Creative Commons Attribution 4.0 International license</a>.
        The data may be used provided the original data
        contributor is cited.
      </div>
      <div>
        For more information on the NMDC Data Policy see
        <a href="https://microbiomedata.org/nmdc-data-use-policy/">
          https://microbiomedata.org/nmdc-data-use-policy/
        </a>
      </div>
    </v-card-text>
    <v-divider />
    <v-card-actions>
      <v-spacer />
      <v-btn
        color="primary"
        text
        :href="href"
        :loading="loading"
        target="_blank"
        rel="noopener"
        @click="$emit('clicked')"
      >
        Accept and continue to download
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
