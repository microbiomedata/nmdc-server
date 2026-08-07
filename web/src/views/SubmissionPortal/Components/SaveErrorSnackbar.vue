<script setup lang="ts">
import { computed, ref } from 'vue';
import { useSubmissionStore } from '../store';

const store = useSubmissionStore();

const dismissedErrorKey = ref<string | null>(null);

const currentErrorKey = computed(() => JSON.stringify([
  store.submission.requests.saving.error,
  store.sampleSet.requests.saving.error,
]));

const hasSaveError = computed(() => (
  store.submission.requests.saving.error !== null ||
  store.sampleSet.requests.saving.error !== null
));

const snackbarVisible = computed({
  get: () => hasSaveError.value && dismissedErrorKey.value !== currentErrorKey.value,
  set: (visible: boolean) => {
    if (!visible) {
      dismissedErrorKey.value = currentErrorKey.value;
    }
  },
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
