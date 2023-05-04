<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { useRouter } from '@/use/useRouter';
import {
  loadRecord, generateRecord,
} from '../store';
import * as api from '../store/api';
import SubmissionTable from './SubmissionTable.vue';

export default defineComponent({
  components: {
    SubmissionTable,
  },

  setup() {
    const router = useRouter();

    async function resume(item: api.MetadataSubmissionRecord) {
      await loadRecord(item.id);
      router?.push({ name: 'Submission Context', params: { id: item.id } });
    }

    async function createNewSubmission() {
      const item = await generateRecord();
      router?.push({ name: 'Submission Context', params: { id: item.id } });
    }

    return {
      createNewSubmission,
      resume,
    };
  },
});
</script>

<template>
  <v-card flat>
    <v-card-title class="text-h4">
      NMDC Submission Portal
    </v-card-title>
    <v-card-text>
      This is the submission portal, where researchers can provide their own study and sample metadata for inclusion in NMDC.
    </v-card-text>
    <v-card-text>
      <v-btn
        color="primary"
        @click="createNewSubmission"
      >
        <v-icon>mdi-plus</v-icon>
        Create New Submission
      </v-btn>
    </v-card-text>
    <v-card-title class="text-h4">
      Past submissions
    </v-card-title>
    <v-card-text>
      Pick up where you left off or review a previous submission.
    </v-card-text>
    <SubmissionTable
      :action-title="`Resume`"
      @submissionSelected="resume"
    />
  </v-card>
</template>
