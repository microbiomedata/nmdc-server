<script lang="ts">
import {
  defineComponent, ref, watch,
} from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { useRouter } from '@/use/useRouter';
import usePaginatedResults from '@/use/usePaginatedResults';
import {
  loadRecord, generateRecord, submissionStatus,
} from '../store';
import * as api from '../store/api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';
import SubmissionTable from './SubmissionTable.vue';

const headers: DataTableHeader[] = [
  {
    text: 'Study Name',
    value: 'metadata_submission.studyForm.studyName',
    sortable: false,
  },
  {
    text: 'Author',
    value: 'author.name',
    sortable: false,
  },
  {
    text: 'Template',
    value: 'metadata_submission.templates',
    sortable: false,
  },
  {
    text: 'Status',
    value: 'status',
    sortable: false,
  },
  {
    text: 'Created',
    value: 'created',
    sortable: false,
  },
  {
    text: '',
    value: 'action',
    align: 'end',
    sortable: false,
  },
];

export default defineComponent({
  components: {
    SubmissionTable,
  },

  setup() {
    const router = useRouter();
    const itemsPerPage = 10;
    const options = ref({
      page: 1,
      itemsPerPage,
    });

    function getStatus(item: api.MetadataSubmissionRecord) {
      const color = item.status === submissionStatus.Complete ? 'success' : 'default';
      return {
        text: item.status,
        color,
      };
    }

    async function resume(item: api.MetadataSubmissionRecord) {
      await loadRecord(item.id);
      router?.push({ name: 'Submission Context', params: { id: item.id } });
    }

    async function createNewSubmission() {
      const item = await generateRecord();
      router?.push({ name: 'Submission Context', params: { id: item.id } });
    }

    const submission = usePaginatedResults(ref([]), api.listRecords, ref([]), itemsPerPage);
    watch(options, () => submission.setPage(options.value.page), { deep: true });

    return {
      HARMONIZER_TEMPLATES,
      createNewSubmission,
      getStatus,
      resume,
      headers,
      options,
      submission,
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
