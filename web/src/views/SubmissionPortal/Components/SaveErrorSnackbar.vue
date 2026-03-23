<script setup lang="ts">
import { incrementalSaveRecordRequest } from '@/views/SubmissionPortal/store';
import { ref, watch } from 'vue';

const snackbarVisible = ref(incrementalSaveRecordRequest.error.value !== null);

watch(() => incrementalSaveRecordRequest.error.value, (newError) => {
  snackbarVisible.value = newError !== null;
});
</script>

<template>
  <v-snackbar
    v-model="snackbarVisible"
    location="top"
    color="error"
    timeout="-1"
  >
    <div class="text-h6">
      Error saving submission
    </div>
    <div class="text-body-2">
      Your latest changes could not be saved. If the problem persists, please
      <a
        style="color: inherit"
        href="mailto:support@microbiomedata.org"
      >contact support</a>.
    </div>
    <template #actions>
      <v-btn
        icon="mdi-close"
        @click="snackbarVisible = false"
      />
    </template>
  </v-snackbar>
</template>
