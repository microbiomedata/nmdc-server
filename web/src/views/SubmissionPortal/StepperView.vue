<script setup lang="ts">
import { computed } from 'vue';

import SubmissionNavigationSidebar from './Components/SubmissionNavigationSidebar.vue';
import { unlockSubmission } from './store/api';
import SaveErrorSnackbar from '@/views/SubmissionPortal/Components/SaveErrorSnackbar.vue';
import SubmissionUneditableBanner from './Components/SubmissionUneditableBanner.vue';
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

const loading = computed(() => (
  store.submission.requests.loading.loading ||
  store.submission.requests.saving.loading ||
  store.sampleSet.requests.loading.loading ||
  store.sampleSet.requests.saving.loading
));
</script>

<template>
  <div class="position-relative">
    <v-progress-linear
      :active="loading"
      absolute
      indeterminate
      color="primary"
    />
    <SaveErrorSnackbar/>
    <SubmissionNavigationSidebar class="mx-0"/>
    <SubmissionUneditableBanner :allowed-roles="['owner', 'editor']"/>
    <v-container>
      <router-view/>
    </v-container>
  </div>
</template>
