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
  sampleSetId: string | null;
}>();

useEventListener('beforeunload', () => {
  if (props.id) {
    unlockSubmission(props.id);
  }
})

const store = useSubmissionStore();
const route = useRoute();

// Sample-set route data is ready once no request is in progress and either no
// sample set was requested or the loaded record matches the requested ID.
// Checking the ID prevents the route component from mounting in the gap between
// the request settling and the store being hydrated, when SubmissionForm could
// erroneously validate the default values.
const sampleSetReady = computed(() =>
  !store.sampleSet.requests.loading.loading &&
  (props.sampleSetId === null || store.sampleSet.record?.id === props.sampleSetId)
);
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

  <!-- Once sample-set route data is ready, render the router view directly if the
       route requested a full-width layout; otherwise wrap it in a v-container. -->
  <router-view
    v-else-if="sampleSetReady && useFullWidthLayout"
  />
  <v-container v-else-if="!useFullWidthLayout">
    <router-view v-if="sampleSetReady" />
  </v-container>
</template>
