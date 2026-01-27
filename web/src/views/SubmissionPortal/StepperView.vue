<script lang="ts">
import { computed, defineComponent, PropType } from 'vue';

import OrcidId from '@/components/Presentation/OrcidId.vue';

import { stateRefs } from '@/store';
import SubmissionNavigationSidebar from './Components/SubmissionNavigationSidebar.vue';
import { getSubmissionLockedBy } from './store';
import { unlockSubmission } from './store/api';

export default defineComponent({
  components: { SubmissionNavigationSidebar, OrcidId },

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

    window.addEventListener('beforeunload', () => {
      if (isEditingSubmission.value) {
        if (props.id) {
          unlockSubmission(props.id);
        }
      }
    });

    return { loggedInUserHasLock, getSubmissionLockedBy, isEditingSubmission };
  },

});
</script>

<template>
  <div>
    <SubmissionNavigationSidebar class="mx-0" />
    <v-container v-if="loggedInUserHasLock || !isEditingSubmission">
      <router-view />
    </v-container>
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
