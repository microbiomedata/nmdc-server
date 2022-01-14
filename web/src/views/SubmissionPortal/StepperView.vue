<script lang="ts">
import { defineComponent } from '@vue/composition-api';

import SubmissionStepper from './Components/SubmissionStepper.vue';

export default defineComponent({
  components: { SubmissionStepper },
});
</script>

<template>
  <div>
    <SubmissionStepper class="mx-0" />
    <v-container>
      <router-view />
    </v-container>
  </div>
</template>
