<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

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
const route = useRoute();
const sampleSetLoading = computed(() => store.sampleSet.requests.loading.loading);
const sampleSetError = computed(() => store.sampleSet.requests.loading.error);
const useFullWidthLayout = computed(() => route.meta.fullWidth === true);
</script>

<template>
  <!-- Common elements that are always shown -->
  <SaveErrorSnackbar />
  <SubmissionNavigationSidebar />

  <!-- If the sample set failed to load, show an error message in a v-container -->
  <v-container v-if="sampleSetError">
    <v-alert
      type="error"
    >
      <div class="text-h6">
        Error loading sample set
      </div>
      {{ sampleSetError }}
    </v-alert>
  </v-container>

  <!-- Unless a sample set is loading, render the router view directly if the route
       requested a full-width layout, otherwise wrap it in a v-container -->
  <router-view
    v-else-if="!sampleSetLoading && useFullWidthLayout"
  />
  <v-container v-else-if="!useFullWidthLayout">
    <router-view v-if="!sampleSetLoading" />
  </v-container>
</template>
