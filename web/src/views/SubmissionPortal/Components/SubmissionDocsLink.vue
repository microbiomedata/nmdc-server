<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';

export default defineComponent({
  props: {
    baseUrl: {
      type: String,
      default: 'https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/submit2nmdc.html',
    },
    anchor: {
      type: String,
      default: '',
    },
  },
  setup(props) {
    const fullUrl = computed(() => props.baseUrl + (props.anchor ? `#${props.anchor}` : ''));
    return {
      fullUrl,
    };
  },
});
</script>

<template>
  <a
    class="ml-2"
    :href="fullUrl"
    target="_blank"
  >
    <v-icon>
      mdi-information-outline
    </v-icon>
  </a>
</template>
