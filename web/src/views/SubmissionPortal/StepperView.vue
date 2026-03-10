<script lang="ts">
import { computed, defineComponent, PropType } from 'vue';

import OrcidId from '@/components/Presentation/OrcidId.vue';

import { stateRefs } from '@/store';
import SubmissionNavigationSidebar from './Components/SubmissionNavigationSidebar.vue';
import {
  canEditSubmissionByStatus,
  canEditSubmissionMetadata,
  getSubmissionLockedBy,
  incrementalSaveRecordRequest
} from './store';
import { unlockSubmission } from './store/api';
import SubmissionPermissionBanner from '@/views/SubmissionPortal/Components/SubmissionPermissionBanner.vue';
import StatusAlert from '@/views/SubmissionPortal/Components/StatusAlert.vue';

export default defineComponent({
  components: {StatusAlert, SubmissionPermissionBanner, SubmissionNavigationSidebar, OrcidId },

  props: {
    id: {
      type: String as PropType<string | null>,
      default: null,
    },
  },

  setup(props) {
    const loggedInUserHasLock = computed(() => {
      const lockedByUser = getSubmissionLockedBy();
      if (!lockedByUser) {
        return true;
      }
      if (lockedByUser.orcid === stateRefs.user.value?.orcid) {
        return true;
      }
      return false;
    });

    const isEditingSubmission = computed(() => props.id !== null);
    const showPermissionBanner = computed(() => canEditSubmissionByStatus() && !canEditSubmissionMetadata());
    const showStatusAlert = computed(() => !canEditSubmissionByStatus());

    window.addEventListener('beforeunload', () => {
      if (isEditingSubmission.value) {
        if (props.id) {
          unlockSubmission(props.id);
        }
      }
    });

    return {
      loggedInUserHasLock,
      getSubmissionLockedBy,
      isEditingSubmission,
      showPermissionBanner,
      showStatusAlert,
      incrementalSaveRecordRequest
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
    <SubmissionNavigationSidebar class="mx-0" />
    <div v-if="loggedInUserHasLock || !isEditingSubmission">
      <SubmissionPermissionBanner v-if="showPermissionBanner" />
      <StatusAlert v-if="showStatusAlert" />
      <v-container>
        <router-view />
      </v-container>
    </div>
    <v-alert v-else>
      <p class="text-h5">
        This submission is currently being edited by:
      </p>
      <orcid-id
        v-if="getSubmissionLockedBy()"
        :orcid-id="getSubmissionLockedBy()?.orcid || ''"
        :name="getSubmissionLockedBy()?.name"
        :authenticated="true"
      />
      <router-link :to="'/submission/home'">
        Return to submission list
      </router-link>
    </v-alert>
  </div>
</template>
