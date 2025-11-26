<script lang="ts">
import {
  defineComponent, ref, watch,
} from 'vue';
import { useRouter } from 'vue-router';
import { DataTableHeader } from 'vuetify';
import usePaginatedResults from '@/use/usePaginatedResults';
import {
  generateRecord, SubmissionStatusEnum, editablebyStatus, SubmissionStatusTitleMapping,
} from '../store';
import * as api from '../store/api';
import OrcidId from '../../../components/Presentation/OrcidId.vue';
import TitleBanner from '@/views/SubmissionPortal/Components/TitleBanner.vue';
import IconBar from '@/views/SubmissionPortal/Components/IconBar.vue';
import IntroBlurb from '@/views/SubmissionPortal/Components/IntroBlurb.vue';
import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';
import { SearchParams } from '@/data/api';
import { addSubmissionRole, deleteSubmission, updateSubmissionStatus } from '../store/api';
import {
  HARMONIZER_TEMPLATES,
  MetadataSubmissionRecord,
  MetadataSubmissionRecordSlim,
  PaginatedResponse,
} from '@/views/SubmissionPortal/types';
import { stateRefs } from '@/store';
import useRequest from '@/use/useRequest';

const headers: DataTableHeader[] = [
  {
    title: 'Study Name',
    value: 'study_name',
    sortable: true,
  },
  {
    title: 'Author',
    value: 'author.name',
    sortable: true,
  },
  {
    title: 'Template',
    value: 'templates',
    sortable: true,
  },
  {
    title: 'Status',
    value: 'status',
    width: '200px',
    sortable: true,
  },
  {
    title: 'Last Modified',
    value: 'date_last_modified',
    sortable: true,
  },
  {
    title: '',
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
    const defaultSortBy = 'date_last_modified';
    const defaultSortOrder = 'desc';
    const options = ref({
      page: 1,
      itemsPerPage,
      sortBy: [{ key: defaultSortBy, order: defaultSortOrder }],
      groupBy: {},
      search: null,
    });
    const isDeleteDialogOpen = ref(false);
    const deleteDialogSubmission = ref<MetadataSubmissionRecordSlim | null>(null);
    const isReviewerAssignmentDialogOpen = ref(false);
    const selectedSubmission = ref<MetadataSubmissionRecordSlim | null>(null);
    const currentUser = stateRefs.user;
    const isTestFilter = ref(null);
    const testFilterValues = [
      { text: 'Show all submissions', val: null },
      { text: 'Show only test submissions', val: true },
      { text: 'Hide test submissions', val: false }];

    const exclude = [SubmissionStatusEnum.InProgress.text, SubmissionStatusEnum.SubmittedPendingReview.text];
    const availableStatuses = Object.keys(SubmissionStatusTitleMapping).map((key) => ({
      value: key,
      text: SubmissionStatusTitleMapping[key as keyof typeof SubmissionStatusTitleMapping],
      disabled: exclude.includes(key),
    }));

    async function getSubmissions(params: SearchParams): Promise<PaginatedResponse<MetadataSubmissionRecordSlim>> {
      return api.listRecords(params, isTestFilter.value);
    }

    function getStatus(item: MetadataSubmissionRecord) {
      const color = item.status === SubmissionStatusEnum.Released.text ? 'success' : 'default';
      return {
        text: SubmissionStatusTitleMapping[item.status as keyof typeof SubmissionStatusTitleMapping] || item.status,
        color,
      };
    }

    async function resume(item: MetadataSubmissionRecord) {
      router?.push({ name: 'Study Form', params: { id: item.id } });
    }

    async function createNewSubmission(isTestSubmission: boolean) {
      const item = await generateRecord(isTestSubmission);
      router?.push({ name: 'Study Form', params: { id: item.id } });
    }

    const submission = usePaginatedResults(ref([]), getSubmissions, ref([]), itemsPerPage);

    function applySortOptions() {
      const sortOrder = options.value.sortBy[0] ? options.value.sortBy[0].order : defaultSortOrder;
      const sortBy = options.value.sortBy[0] ? options.value.sortBy[0].key : defaultSortBy;
      submission.setSortOptions(sortBy, sortOrder);
    }

    applySortOptions();
    const assignReviewerRequest = useRequest();

    async function handleStatusChange(item: MetadataSubmissionRecordSlim, newStatus: string) {
      await updateSubmissionStatus(item.id, newStatus);
      await submission.refetch();
    }

    function updateTableOptions(newOptions: any) {
      options.value = newOptions;
      submission.setPage(options.value.page);
      applySortOptions();
    }
    
    watch(isTestFilter, () => {
      options.value.page = 1;
      submission.setPage(options.value.page);
      applySortOptions();
    }, { deep: true });

    function handleOpenDeleteDialog(item: MetadataSubmissionRecordSlim | null) {
      deleteDialogSubmission.value = item;
      if (deleteDialogSubmission.value) {
        isDeleteDialogOpen.value = true;
      }
    }

    async function handleDelete(item: MetadataSubmissionRecordSlim | null) {
      if (!item) {
        return;
      }
      await deleteSubmission(item.id);
      submission.refetch();
      deleteDialogSubmission.value = null;
      isDeleteDialogOpen.value = false;
    }

    const reviewerOrcid = ref('');
    function openReviewerDialog(item: MetadataSubmissionRecordSlim | null) {
      isReviewerAssignmentDialogOpen.value = true;
      selectedSubmission.value = item;
    }

    async function addReviewer() {
      await assignReviewerRequest.request(async () => {
        if (!selectedSubmission.value) {
          return;
        }
        await addSubmissionRole(selectedSubmission.value.id, reviewerOrcid.value, 'reviewer');
      });
      isReviewerAssignmentDialogOpen.value = false;
    }

    return {
      HARMONIZER_TEMPLATES,
      isDeleteDialogOpen,
      isTestFilter,
      deleteDialogSubmission,
      currentUser,
      assignReviewerRequest,
      isReviewerAssignmentDialogOpen,
      reviewerOrcid,
      IconBar,
      IntroBlurb,
      TitleBanner,
      createNewSubmission,
      editablebyStatus,
      getStatus,
      resume,
      addReviewer,
      handleDelete,
      handleOpenDeleteDialog,
      openReviewerDialog,
      headers,
      options,
      submission,
      testFilterValues,
      availableStatuses,
      handleStatusChange,
      SubmissionStatusEnum,
      updateTableOptions,
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
      <template #activator="{ props }">
        <v-btn
          color="primary"
          large
          class="mr-0"
          style="transform:translateY(-50%) rotate(-90deg); right: -50px; top: 50%; position: fixed; z-index: 100;"
          v-bind="props"
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
          @click="createNewSubmission(false)"
        >
          <v-icon>mdi-plus</v-icon>
          Create Submission
        </v-btn>
        <v-btn
          color="primary"
          class="ml-3"
          variant="outlined"
          @click="createNewSubmission(true)"
        >
          <v-icon>mdi-plus</v-icon>
          Create Test Submission
        </v-btn>
        <v-tooltip right>
          <template #activator="{ props }">
            <v-icon
              class="pl-2"
              color="primary"
              v-bind="props"
            >
              mdi-information
            </v-icon>
          </template>
          <span>Test submissions should be used when at a workshop or doing a test, example, or training. These cannot be submitted.</span>
        </v-tooltip>
      </v-card-text>
      <v-card-title class="text-h4">
        Past submissions
      </v-card-title>
      <v-row
        justify="space-between"
        class="pb-2"
        no-gutters
      >
        <v-col
          cols="5"
        >
          <v-card-text>
            Pick up where you left off or review a previous submission.
          </v-card-text>
        </v-col>
        <v-col
          cols="3"
        >
          <v-select
            v-model="isTestFilter"
            :items="testFilterValues"
            item-title="text"
            item-value="val"
            label="Test Submissions"
            variant="outlined"
            hide-details
          />
        </v-col>
      </v-row>
      <v-card variant="outlined">
        <v-data-table-server
          v-model:items-per-page="submission.data.limit"
          :headers="headers"
          :items="submission.data.results.results"
          :items-length="submission.data.results.count"
          :loading="submission.loading.value"
          :footer-props="{ itemsPerPageOptions: [10, 20, 50] }"
          @update:options="updateTableOptions"
        >
          <template #[`item.study_name`]="{ item }">
            {{ item.study_name }}
            <v-chip
              v-if="item.is_test_submission"
              color="orange"
              text-color="white"
              small
            >
              TEST
            </v-chip>
          </template>
          <template #[`item.author.name`]="{ item }">
            <orcid-id
              :orcid-id="item.author.orcid"
              :name="item.author.name"
              :width="14"
              :authenticated="true"
            />
          </template>
          <template #[`item.templates`]="{ item }">
            {{ item.templates.map((template) => HARMONIZER_TEMPLATES[template]?.displayName).join(' + ') }}
          </template>
          <template #[`item.date_last_modified`]="{ item }">
            {{ new Date(item.date_last_modified + 'Z').toLocaleString() }}
          </template>
          <template #[`header.status`]="{ column, getSortIcon, toggleSort }">
            <div class="d-flex align-center ga-1">
              <v-tooltip
                v-if="currentUser?.is_admin"
                location="bottom"
              >
                <template #activator="{ props }">
                  <v-icon
                    class="ml-1"
                    color="grey"
                    v-bind="props"
                  >
                    mdi-information-outline
                  </v-icon>
                </template>
                <span>Greyed out options are user-triggered statuses and cannot be changed or selected</span>
              </v-tooltip>
              <span>
                {{ column.title }}
              </span>
              <v-icon
                class="v-data-table-header__sort-icon"
                :icon="getSortIcon(column)"
                @click="toggleSort(column)"
              />
            </div>
          </template>
          <template #[`item.status`]="{ item }">
            <div class="d-flex align-center">
              <v-select
                v-if="currentUser?.is_admin && item.status === SubmissionStatusEnum.InProgress.text"
                :value="item.status"
                :items="availableStatuses"
                item-title="text"
                item-value="value"
                item-disabled="disabled"
                dense
                hide-details
                disabled
              >
                <template #selection="{ item: statusItem }">
                  {{ statusItem.title }}
                </template>
              </v-select>
              <v-select
                v-else-if="currentUser?.is_admin"
                :value="item.status"
                :items="availableStatuses"
                item-title="text"
                item-value="value"
                item-disabled="disabled"
                dense
                hide-details
                @change="(newStatus: string) => handleStatusChange(item, newStatus)"
              >
                <template #selection="{ item: statusItem }">
                  {{ statusItem.title }}
                </template>
              </v-select>
              <v-chip
                v-else
                :color="getStatus(item as MetadataSubmissionRecord).color"
              >
                {{ getStatus(item as MetadataSubmissionRecord).text }}
              </v-chip>
            </div>
          </template>
          <template #[`item.action`]="{ item }">
            <div class="d-flex align-center">
              <v-spacer />
              <v-btn
                size="small"
                color="primary"
                @click="() => resume(item as MetadataSubmissionRecord)"
              >
                <span v-if="editablebyStatus(item.status)">
                  Resume
                  <v-icon class="pl-1">mdi-arrow-right-circle</v-icon>
                </span>
                <span v-else>
                  <v-icon class="pl-1">mdi-eye</v-icon>
                  View
                </span>
              </v-btn>
              <v-menu
                offset-x
              >
                <template #activator="{ props }">
                  <v-btn
                    variant="text"
                    icon
                    class="ml-1"
                    v-bind="props"
                  >
                    <v-icon>
                      mdi-dots-vertical
                    </v-icon>
                  </v-btn>
                </template>
                <v-list>
                  <v-list-item
                    @click="() => handleOpenDeleteDialog(item)"
                  >
                    <v-list-item-title>Delete</v-list-item-title>
                  </v-list-item>
                  <v-list-item
                    v-if="currentUser?.is_admin"
                    @click="() => openReviewerDialog(item)"
                  >
                    <v-list-item-title>Assign Reviewer</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
          </template>
        </v-data-table-server>
      </v-card>
    </v-card>
    <v-dialog
      v-model="isDeleteDialogOpen"
      :width="550"
    >
      <v-card>
        <v-spacer />
        <v-card-title class="text-h5">
          Delete Submission
        </v-card-title>
        <v-card-text class="text-h5">
          <p v-if="deleteDialogSubmission && deleteDialogSubmission.study_name != ''">
            This will delete "{{ deleteDialogSubmission.study_name }}" and all associated data.
          </p>
          <p v-else>
            This will delete this submission and all associated data.
          </p>
          <p>This cannot be undone.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            class="ma-3"
            @click="isDeleteDialogOpen = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="red"
            class="ml-3 white--text"
            @click="handleDelete(deleteDialogSubmission)"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog
      v-model="isReviewerAssignmentDialogOpen"
      max-width="600px"
    >
      <v-card>
        <v-card-title class="text-h5">
          Assign Reviewer
        </v-card-title>
        <v-card-text
          class="pb-0"
        >
          <v-row
            no-gutters
          >
            <legend>
              Please enter the reviewer's ORCiD below. This will give the reviewer the ability to view, approve and run scripts on this submission.
            </legend>
            <v-col cols="4">
              <v-text-field
                v-model="reviewerOrcid"
                class="mt-4"
                label="ORCiD"
                variant="outlined"
                dense
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions
          class="pt-0"
        >
          <v-btn
            class="ma-3"
            @click="isReviewerAssignmentDialogOpen = false"
          >
            Cancel
          </v-btn>
          <v-spacer />

          <v-btn
            color="primary"
            class="mt-2"
            :loading="assignReviewerRequest.loading.value"
            @click="() => addReviewer()"
          >
            Assign Reviewer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
