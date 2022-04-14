<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { useRouter } from '@/use/useRouter';
import {
  pastSubmissions, populateList, loadRecord, generateRecord,
} from '../store';
import * as api from '../store/api';

const headers: DataTableHeader[] = [
  {
    text: 'Study Name',
    value: 'metadata_submission.studyForm.studyName',
  },
  {
    text: 'PI Name',
    value: 'metadata_submission.studyForm.piName',
  },
  {
    text: 'Template',
    value: 'metadata_submission.template',
  },
  {
    text: 'Status',
    value: 'status',
  },
  {
    text: '',
    value: 'action',
    align: 'end',
  },
];

export default defineComponent({
  setup() {
    const router = useRouter();

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
      router?.push({ name: 'Study Form', params: { id: item.id } });
    }

    async function createNewSubmission() {
      const item = await generateRecord();
      router?.push({ name: 'Study Form', params: { id: item.id } });
    }

    populateList();

    return {
      createNewSubmission,
      getStatus,
      resume,
      headers,
      pastSubmissions,
    };
  },
});
</script>

<template>
  <v-card flat>
    <v-card-title class="text-h4">
      NMDC Metadata Submission Portal
    </v-card-title>
    <v-card-text>
      This is the metadata submission portal, where researchers can provide their own study and sample metadata for inclusion in NMDC.
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
        :items="pastSubmissions"
      >
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
