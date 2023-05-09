<script lang="ts">
import { defineComponent, ref, watch } from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import usePaginatedResults from '@/use/usePaginatedResults';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';
import { submissionStatus } from '../store';
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
  props: {
    actionTitle: {
      type: String,
      required: true,
    },
  },
  setup() {
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

    const submission = usePaginatedResults(ref([]), api.listRecords, ref([]), itemsPerPage);
    watch(options, () => submission.setPage(options.value.page), { deep: true });

    return {
      HARMONIZER_TEMPLATES,
      getStatus,
      headers,
      options,
      submission,
    };
  },
});
</script>

<template>
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
      <template #[`item.metadata_submission.templates`]="{ item }">
        {{ item.metadata_submission.templates.map((template) => HARMONIZER_TEMPLATES[template].displayName).join(' + ') }}
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
          @click="$emit('submissionSelected', item)"
        >
          {{ actionTitle }}
          <v-icon class="pl-1">
            mdi-arrow-right-circle
          </v-icon>
        </v-btn>
      </template>
    </v-data-table>
  </v-card>
</template>
