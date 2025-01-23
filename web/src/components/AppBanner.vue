<script lang="ts">
import { computed, defineComponent } from 'vue';
import { stateRefs } from '@/store';

export default defineComponent({
  setup() {
    const message = stateRefs.bannerMessage;
    const title = stateRefs.bannerTitle;
    const showAppBanner = computed(() => message.value || title.value);
    return { showAppBanner, message, title };
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
      class="text-h6"
    >
      {{ title || '' }}
    </p>
    <p>
      {{ message || '' }}
    </p>
  </v-banner>
</template>
