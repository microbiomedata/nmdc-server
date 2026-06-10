<script setup lang="ts">
import { computed } from 'vue';

import SubmissionNavigationSidebar from './Components/SubmissionNavigationSidebar.vue';
import { unlockSubmission } from './store/api';
import SaveErrorSnackbar from '@/views/SubmissionPortal/Components/SaveErrorSnackbar.vue';
import { useEventListener } from '@vueuse/core';
import { useSubmissionStore } from './store';

const props = defineProps<{
  id: string | null;
}>();

useEventListener('beforeunload', () => {
  if (props.id) {
    unlockSubmission(props.id);
  }
})

const store = useSubmissionStore();
const sampleSetLoading = computed(() => store.sampleSet.requests.loading.loading);
const sampleSetError = computed(() => store.sampleSet.requests.loading.error);
</script>

<template>
  <SaveErrorSnackbar />
  <SubmissionNavigationSidebar class="mx-0" />
  <v-container>
    <v-alert
      v-if="sampleSetError"
      type="error"
    >
      <div class="text-h6">
        Error loading sample set
      </div>
      {{ sampleSetError }}
    </v-alert>
    <router-view v-else-if="!sampleSetLoading" />
  </v-container>
</template>
