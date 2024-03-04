<script lang="ts">
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  setup() {
    return {};
  },
});
</script>

<template>
  <v-alert
    type="info"
  >
    Your current permission level for this submission does not allow editing of this page. Contact the submission author to request a change in permission level.
  </v-alert>
</template>
