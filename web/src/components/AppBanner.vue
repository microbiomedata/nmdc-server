<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';

export default defineComponent({
  setup() {
    const showAppBanner = ref(true);
    return { showAppBanner };
  },
});
</script>

<template>
  <v-banner
    v-if="showAppBanner"
    color="blue"
    dark
    icon="mdi-information"
    class="ma-4"
  >
    <p
      class="title"
    >
      Banner title (replace me)
    </p>
    <p>
      Banner content (replace me)
    </p>
  </v-banner>
</template>
