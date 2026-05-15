<script lang="ts">
import { defineComponent, PropType } from 'vue';

import SubmissionNavigationSidebar from './Components/SubmissionNavigationSidebar.vue';
import { incrementalSaveRecordRequest } from './store';
import { unlockSubmission } from './store/api';
import SaveErrorSnackbar from '@/views/SubmissionPortal/Components/SaveErrorSnackbar.vue';
import SubmissionUneditableBanner from './Components/SubmissionUneditableBanner.vue';

export default defineComponent({
  components: {
    SaveErrorSnackbar,
    SubmissionNavigationSidebar,
    SubmissionUneditableBanner,
  },

  props: {
    id: {
      type: String as PropType<string | null>,
      default: null,
    },
  },

  setup(props) {
    window.addEventListener('beforeunload', () => {
      if (props.id) {
        unlockSubmission(props.id);
      }
    });

    return {
      incrementalSaveRecordRequest,
    };
  },

});
</script>

<template>
  <div class="position-relative">
    <v-progress-linear
      :active="incrementalSaveRecordRequest.loading.value"
      absolute
      indeterminate
      color="primary"
    />
    <SaveErrorSnackbar />
    <SubmissionNavigationSidebar class="mx-0" />
    <SubmissionUneditableBanner minimum-permission-level="editor" />
    <v-container>
      <router-view />
    </v-container>
  </div>
</template>
