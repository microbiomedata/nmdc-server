<script lang="ts">
import {
  defineComponent, ref, watch, Ref,
} from '@vue/composition-api';
import { DataOptions, DataTableHeader } from 'vuetify';
import { useRouter } from '@/use/useRouter';
import usePaginatedResults from '@/use/usePaginatedResults';
import {
  generateRecord, submissionStatus,
} from '../store';
import * as api from '../store/api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';
import OrcidId from '../../../components/Presentation/OrcidId.vue';
import TitleBanner from '@/views/SubmissionPortal/Components/TitleBanner.vue';
import IconBar from '@/views/SubmissionPortal/Components/IconBar.vue';
import IntroBlurb from '@/views/SubmissionPortal/Components/IntroBlurb.vue';
import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';

const headers: DataTableHeader[] = [
  {
    text: 'Study Name',
    value: 'study_name',
  },
  {
    text: 'Author',
    value: 'author.name',
  },
  {
    text: 'Template',
    value: 'templates',
  },
  {
    text: 'Status',
    value: 'status',
  },
  {
    text: 'Created',
    value: 'created',
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
    IconBar, IntroBlurb, OrcidId, TitleBanner, ContactCard,
  },
  setup() {
    const router = useRouter();
    const itemsPerPage = 10;
    const options: Ref<DataOptions> = ref<DataOptions>({
      page: 1,
      itemsPerPage,
      sortBy: ['created'],
      sortDesc: [true],
      groupBy: [],
      groupDesc: [],
      multiSort: false,
      mustSort: false,
    });

    function getStatus(item: api.MetadataSubmissionRecord) {
      const color = item.status === submissionStatus.Complete ? 'success' : 'default';
      return {
        text: item.status,
        color,
      };
    }

    async function resume(item: api.MetadataSubmissionRecord) {
      router?.push({ name: 'Submission Context', params: { id: item.id } });
    }

    async function createNewSubmission() {
      const item = await generateRecord();
      router?.push({ name: 'Submission Context', params: { id: item.id } });
    }

    const submission = usePaginatedResults(ref([]), api.listRecords, ref([]), itemsPerPage);
    watch(options, () => {
      submission.setPage(options.value.page);
      const sortOrder = options.value.sortDesc[0] ? 'desc' : 'asc';
      submission.setSortOptions(options.value.sortBy[0], sortOrder);
    }, { deep: true });

    return {
      HARMONIZER_TEMPLATES,
      IconBar,
      IntroBlurb,
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
  <div>
    <v-menu
      offset-x
      left
    >
      <template #activator="{on, attrs}">
        <v-btn
          color="primary"
          large
          class="mr-0"
          style="transform:translateY(-50%) rotate(-90deg); right: -50px; top: 50%; position: fixed; z-index: 100;"
          v-bind="attrs"
          v-on="on"
        >
          support
          <v-icon
            class="ml-2"
            style="transform: rotate(90deg);"
          >
            mdi-message-question
          </v-icon>
        </v-btn>
      </template>
      <ContactCard />
    </v-menu>
    <v-card flat>
      <v-card-text class="pt-0 px-0">
        <v-container>
          <v-row>
            <v-col class="pb-0">
              <TitleBanner />
              <IconBar />
            </v-col>
          </v-row>
          <v-row v-if="submission.data.results.count === 0">
            <v-col>
              <IntroBlurb />
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
          <template #[`item.templates`]="{ item }">
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
  </div>
</template>
