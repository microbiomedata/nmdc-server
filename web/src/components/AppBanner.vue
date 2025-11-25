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
  <v-alert
    v-if="showAppBanner"
    :title="title || undefined"
    :text="message || undefined"
    color="blue"
    icon="mdi-information"
    class="ma-4"
  />
</template>
