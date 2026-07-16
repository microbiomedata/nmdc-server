<script setup lang="ts">
import { ref, useTemplateRef, watch } from 'vue';
import { useRouter } from 'vue-router';
import { DataTableHeader } from 'vuetify';
import { VTextField } from 'vuetify/components';
import usePaginatedResults from '@/use/usePaginatedResults';
import * as api from '../store/api';
import OrcidId from '../../../components/Presentation/OrcidId.vue';
import TitleBanner from '@/views/SubmissionPortal/Components/TitleBanner.vue';
import IconBar from '@/views/SubmissionPortal/Components/IconBar.vue';
import IntroBlurb from '@/views/SubmissionPortal/Components/IntroBlurb.vue';
import ContactCard from '@/views/SubmissionPortal/Components/ContactCard.vue';
import { SearchParams } from '@/data/api';
import { addSubmissionRole, deleteSubmission } from '../store/api';
import {
  PaginatedResponse,
  SubmissionMetadataSlim,
} from '@/views/SubmissionPortal/types';
import { stateRefs } from '@/store';
import { validateOrcid } from '../utils.ts';
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
const deleteDialogSubmission = ref<SubmissionMetadataSlim | null>(null);
const isReviewerAssignmentDialogOpen = ref(false);
const isReviewerAssignmentSnackbarOpen = ref(false);
const selectedSubmission = ref<SubmissionMetadataSlim | null>(null);
const currentUser = stateRefs.user;
const isTestFilter = ref(null);
const testFilterValues = [
  { text: 'Show all submissions', val: null },
  { text: 'Show only test submissions', val: true },
  { text: 'Hide test submissions', val: false }];
const searchText = ref('');

async function getSubmissions(params: SearchParams): Promise<PaginatedResponse<SubmissionMetadataSlim>> {
  return api.listSubmissions(params, isTestFilter.value, searchText.value);
}


async function resume(item: SubmissionMetadataSlim) {
  router?.push({ name: 'Submission Summary', params: { id: item.id } });
}

const submission = usePaginatedResults(ref([]), getSubmissions, ref([]), itemsPerPage);

function applySortOptions() {
  const sortOrder = options.value.sortBy[0] ? options.value.sortBy[0].order : defaultSortOrder;
  const sortBy = options.value.sortBy[0] ? options.value.sortBy[0].key : defaultSortBy;
  submission.setSortOptions(sortBy, sortOrder);
}

applySortOptions();
const assignReviewerRequest = useRequest();

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

watch(searchText, () => {
  options.value.page = 1;
  submission.setPage(options.value.page);
  applySortOptions();
});

function handleOpenDeleteDialog(item: SubmissionMetadataSlim | null) {
  deleteDialogSubmission.value = item;
  if (deleteDialogSubmission.value) {
    isDeleteDialogOpen.value = true;
  }
}

async function handleDelete(item: SubmissionMetadataSlim | null) {
  if (!item) {
    return;
  }
  await deleteSubmission(item.id);
  submission.refetch();
  deleteDialogSubmission.value = null;
  isDeleteDialogOpen.value = false;
}

const reviewerOrcid = ref('');
const orcidTextFieldRef = useTemplateRef<InstanceType<typeof VTextField>>('orcidTextField');

function openReviewerDialog(item: SubmissionMetadataSlim | null) {
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
  isReviewerAssignmentSnackbarOpen.value = true;
  reviewerOrcid.value = '';
  isReviewerAssignmentDialogOpen.value = false;
}

</script>

<template>
  <div>
    <v-menu
      offset-x
      location="left"
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
    <v-container>
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
            :to="{ name: 'Create Submission' }"
          >
            <v-icon>mdi-plus</v-icon>
            Create Submission
          </v-btn>
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
            <v-text-field
              v-model="searchText"
              label="Search"
              variant="outlined"
              class="pr-2"
              placeholder="Search by study name or author"
              persistent-placeholder
              hide-details
              clearable
            />
          </v-col>
          <v-col>
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
            :items-per-page-options="[10, 20, 50]"
            :loading="submission.loading.value"
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
            <template #[`item.date_last_modified`]="{ item }">
              {{ new Date(item.date_last_modified + 'Z').toLocaleString() }}
            </template>
            <template #[`item.action`]="{ item }">
              <div class="d-flex align-center">
                <v-spacer />
                <v-btn
                  size="small"
                  color="primary"
                  @click="() => resume(item)"
                >
                  Resume
                  <v-icon class="pl-1">
                    mdi-arrow-right-circle
                  </v-icon>
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
    </v-container>
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
                ref="orcidTextField"
                v-model="reviewerOrcid"
                class="mt-4"
                label="ORCiD"
                variant="outlined"
                :rules="[(v) => !!v || 'An ORCID iD is required',
                validateOrcid]"
              />
            </v-col>
          </v-row>
          <v-card
            v-if="selectedSubmission?.reviewers?.length"
            class="mt-4"
            variant="outlined"
          >
            <v-card-title class="text-subtitle-1 pb-2">
              Current reviewers
            </v-card-title>
            <v-card-text class="pt-0">
              <div class="d-flex flex-wrap ga-2">
                <v-chip
                  v-for="reviewer in selectedSubmission?.reviewers"
                  :key="reviewer"
                  color="primary"
                  variant="outlined"
                >
                  {{ reviewer }}
                </v-chip>
              </div>
            </v-card-text>
          </v-card>
          <div
            v-else
            class="mt-4 text-body-2 text-medium-emphasis"
          >
            No reviewers have been added yet.
          </div>
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
            :disabled="orcidTextFieldRef?.isValid === false || !reviewerOrcid"
            @click="() => addReviewer()"
          >
            Assign Reviewer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-snackbar
      v-model="isReviewerAssignmentSnackbarOpen"
      location="bottom"
      :color="assignReviewerRequest.error.value ? 'error' : 'success'"
      timeout="3000"
    >
      {{ assignReviewerRequest.error.value ? 'Something went wrong assigning a reviewer.' : 'Reviewer added successfully.' }}
      <template #actions>
        <v-btn
          icon="mdi-close"
          @click="isReviewerAssignmentSnackbarOpen = false"
        />
      </template>
    </v-snackbar>
  </div>
</template>
