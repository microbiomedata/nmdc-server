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
      Upcoming maintenance (January 26 - February 3)
    </p>
    <p>
      Sunday, 01/26/2025 - Sunday, 02/02/2025: Storage system will be undergoing
      scheduled maintenance. Downloading of data files will be disabled.
    </p>
    <p>
      Monday, 02/03/2025 (until 5pm PST): NMDC Data Portal, Submission Portal, and
      API will be offline for software updates.
    </p>
    <p>
      We expect our systems to be back online and fully functional by Monday,
      02/03/2025 at 5pm PST.
    </p>
  </v-banner>
</template>
