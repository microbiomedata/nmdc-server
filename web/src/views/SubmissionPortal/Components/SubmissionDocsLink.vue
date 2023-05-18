<script lang="ts">
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  props: {
    documentationUrl: {
      type: String,
      default: 'https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/submit2nmdc.html',
    },
  },
});
</script>

<template>
  <a
    class="ml-2"
    :href="documentationUrl"
    target="_blank"
  >
    <v-icon>
      mdi-information-outline
    </v-icon>
  </a>
</template>
