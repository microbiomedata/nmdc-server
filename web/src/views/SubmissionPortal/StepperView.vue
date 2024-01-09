<script lang="ts">
import { computed, defineComponent, PropType } from '@vue/composition-api';

import SubmissionStepper from './Components/SubmissionStepper.vue';
import OrcidId from '@/components/Presentation/OrcidId.vue';

import { stateRefs } from '@/store';
import { getSubmissionLockedBy } from './store';
import { useRouter } from '@/use/useRouter';
import { unlockSubmission } from './store/api';

export default defineComponent({
  components: { SubmissionStepper, OrcidId },

  props: {
    id: {
      type: String as PropType<string | null>,
      default: null,
    },
  },

  setup() {
    const router = useRouter();

    const loggedInUserHasLock = computed(() => {
      const lockedByUser = getSubmissionLockedBy();
      if (!lockedByUser) {
        return true;
      }
      if (lockedByUser.orcid === stateRefs.orcid.value) {
        return true;
      }
      return false;
    });

    const isEditingSubmission = computed(() => {
      if (router) {
        return !!router.currentRoute.params.id;
      }
      return false;
    });

    window.addEventListener('beforeunload', () => {
      if (isEditingSubmission.value) {
        if (router) {
          unlockSubmission(router.currentRoute.params.id);
        }
      }
    });

    return { loggedInUserHasLock, getSubmissionLockedBy, isEditingSubmission };
  },

});
</script>

<template>
  <div>
    <SubmissionStepper class="mx-0" />
    <v-container v-if="loggedInUserHasLock || !isEditingSubmission">
      <router-view />
    </v-container>
    <v-alert v-else>
      <p class="text-h5">
        This submission is currently being edited by:
      </p>
      <orcid-id
        v-if="getSubmissionLockedBy()"
        :orcid-id="getSubmissionLockedBy().orcid"
        :name="getSubmissionLockedBy().name"
        authenticated="true"
      />
      <a href="/submission/home">
        Return to submission list
      </a>
    </v-alert>
  </div>
</template>
