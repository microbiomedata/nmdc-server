<script lang="ts">
import {
  defineComponent, ref, watch,
} from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { useRouter } from '@/use/useRouter';
import usePaginatedResults from '@/use/usePaginatedResults';
import {
  loadRecord, generateRecord,
} from '../store';
import * as api from '../store/api';

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
    value: 'metadata_submission.template',
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
  setup() {
    const router = useRouter();
    const itemsPerPage = 10;
    const options = ref({
      page: 1,
      itemsPerPage,
    });

    function getStatus(item: api.MetadataSubmissionRecord) {
      if (item.status === 'complete') {
        return {
          text: 'Complete',
          color: 'success',
        };
      }
      return {
        text: 'In progress',
        color: 'default',
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
    <v-card outlined>
      <v-data-table
        :headers="headers"
        :items="submission.data.results.results"
        :server-items-length="submission.data.results.count"
        :options.sync="options"
        :loading="submission.loading.value"
        :items-per-page.sync="submission.data.limit"
        :footer-props="{ itemsPerPageOptions: [10, 20, 50] }"
      >
        <template #[`item.author.name`]="{ item }">
          <a
            :href="`https://orcid.org/${item.author.orcid}`"
            rel="noopener noreferrer"
            target="_blank"
          >
            {{ item.author.name || item.author.orcid }}
          </a>
        </template>
        <template #[`item.created`]="{ item }">
          {{ new Date(item.created).toLocaleString() }}
        </template>
        <template #[`item.status`]="{ item }">
          <v-chip
            :color="getStatus(item).color"
          >
            {{ getStatus(item).text }}
          </v-chip>
        </template>
        <template #[`item.action`]="{ item }">
          <v-btn
            small
            color="primary"
            @click="() => resume(item)"
          >
            Resume
            <v-icon class="pl-1">
              mdi-arrow-right-circle
            </v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>
  </v-card>
</template>
