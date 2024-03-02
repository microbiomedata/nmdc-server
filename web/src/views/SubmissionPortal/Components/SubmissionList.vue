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
import OrcidId from '../../../components/Presentation/OrcidId.vue';
import TitleBanner from '@/views/SubmissionPortal/Components/TitleBanner.vue';
import IconBar from '@/views/SubmissionPortal/Components/IconBar.vue';

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
  components: { IconBar, OrcidId, TitleBanner },
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
      IconBar,
      TitleBanner,
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
    <v-card-text class="pt-0 px-0">
      <v-container>
        <v-row>
          <v-col class="pb-0">
            <TitleBanner />
            <IconBar />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-container>
              <v-row>
                <v-col class="px-0">
                  <h2 class="blue--text text-h6">
                    Making it easy to follow standards
                  </h2>
                  <p class="text-justify mb-0 text-body-1">
                    The Submission Portal is a flexible, template-driven tool designed to lower the barrier to collecting and reporting cohesive, standardized metadata about studies, samples, and assays. The standards we leverage include:
                  </p>
                </v-col>
              </v-row>
              <v-row>
                <v-col class="px-0">
                  <h2 class="blue--text text-h6">
                    Supporting FAIR data
                  </h2>
                  <p class="text-justify mb-0 text-body-1">
                    The Submission Portal leverages validation functions of the
                    <a
                      href="https://github.com/cidgoh/DataHarmonizer"
                      target="_blank"
                      title="View cidgoh/DataHarmonizer on GitHub"
                    >DataHarmonizer</a>
                    tool to check entered metadata values against the standards in the
                    <a
                      href="https://github.com/microbiomedata/nmdc-schema"
                      target="_blank"
                      title="View microbiomedata/nmdc-schema on GitHub"
                    >NMDC schema</a>.
                    By following existing community standards like the Minimum Information about any (x) Sequence (MIxS) standard from the Genomic Standards Consortium (GSC), the Submission Portal advances FAIR microbiome data.
                  </p>
                </v-col>
              </v-row>
              <v-row>
                <v-col class="px-0">
                  <h2 class="blue--text text-h6">
                    Interoperability with DOE User Facilities
                  </h2>
                  <p class="text-justify mb-0 text-body-1">
                    We collaborate closely with the JGI and EMSL to support integration of multi-omics data generated across these Facilities. The Submission Portal has been designed to be compliant with both JGI and EMSL sample submission requirements, ensuring study and biosample information is consistently collected to support interoperability and reuse.
                  </p>
                </v-col>
              </v-row>
            </v-container>
          </v-col>
        </v-row>
      </v-container>
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
          <orcid-id
            :orcid-id="item.author.orcid"
            :name="item.author.name"
            :width="14"
            :authenticated="true"
          />
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
