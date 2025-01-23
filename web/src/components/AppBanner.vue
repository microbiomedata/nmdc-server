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
      Upcoming maintenance (January 26-February 3)
    </p>
    <p>
      From Sunday, January 26 to Sunday, February 2, our data storage system will be
      undergoing scheduled maintenance. During that time, the downloading of data files
      will be disabled.
    </p>
    <p>
      Then, on Monday, February 3, the NMDC Data Portal and NMDC Submission Portal will be
      undergoing software updates. During that time, both portals will be offline.
    </p>
    <p>
      Both portals will be back online and fully functional by Monday, February 3,
      at 5:00 p.m. Pacific time.
    </p>
  </v-banner>
</template>
