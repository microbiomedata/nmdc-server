<script lang="ts">
import { computed, defineComponent, onUpdated, ref, useTemplateRef } from 'vue';
import { stateRefs } from '@/store';

export default defineComponent({
  setup() {
    const message = stateRefs.bannerMessage;
    const title = stateRefs.bannerTitle;
    const showAppBanner = computed(() => message.value || title.value);

    // Compute the height of the banner on updates and expose it to the parent component as `height`
    const containerElement = useTemplateRef<HTMLDivElement>("container");
    const containerHeight = ref<number>(0);
    onUpdated(() => {
      containerHeight.value = containerElement.value?.offsetHeight || 0;
    })

    return {
      showAppBanner,
      message,
      title,
      height: containerHeight
    };
  },
});
</script>

<template>
  <div ref="container">
    <v-alert
      v-if="showAppBanner"
      :title="title || undefined"
      :text="message || undefined"
      color="blue"
      icon="mdi-information"
      class="ma-4"
    />
  </div>
</template>
