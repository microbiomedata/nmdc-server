<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { stateRefs } from '@/store';
import { DataTableHeader } from 'vuetify';
import { useSubmissionStore } from '../store';
import { listSubmissionSampleSets, getAllStatusTransitions, updateSubmissionSampleSetStatus, deleteSampleSet } from '../store/api';
import { useRouter } from 'vue-router';
import {
  SubmissionStatusEnum,
  SubmissionStatusKey,
  AllowedStatusTransitions,
  SubmissionEditorRole,
  SubmissionSampleSetStatusPatch,
  SubmissionSampleSetListItem,
  StatusOption,
} from '@/views/SubmissionPortal/types.ts';
import PageSection from '@/components/Presentation/PageSection.vue';


const headers: DataTableHeader[] = [
  {
    title: 'Sample Set Name',
    value: 'name',
    sortable: true,
  },
  {
    title: 'Templates',
    value: 'templates',
    sortable: false,
  },
  {
    title: 'Status',
    value: 'status',
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
const store = useSubmissionStore();
const isDeleteDialogOpen = ref(false);
const deleteDialogSubmission = ref<SubmissionSampleSetListItem | null>(null);
const defaultSortBy = 'date_last_modified';
const defaultSortOrder = 'desc';
const itemsPerPage = 10;
const currentUser = stateRefs.user;
const sampleSetEditableState = ref<Record<string, boolean>>({});
const isContributor = computed(() => {
  if (!currentUser.value?.orcid) {
    return false;
  }
  return store.submission.record!.contributors.includes(currentUser.value.orcid);
});


const sampleSet = ref<SubmissionSampleSetListItem[]>([]);
onMounted(async () => {
  sampleSet.value = await listSubmissionSampleSets(store.submission.record!.id);
});

watch(
  sampleSet,
  (newList) => {
    const editableStatuses = ['InProgress', 'UpdatesRequired'];
    for (const sampSet of newList) {
      sampleSetEditableState.value[sampSet.id] = editableStatuses.includes(sampSet.status)
    }
  },
  { deep: true }
);

//const options = ref({
//    page: 1,
//    itemsPerPage,
//    sortBy: [{ key: defaultSortBy, order: defaultSortOrder }],
//    groupBy: {},
//    search: null,
//    });

function getStatus( status: SubmissionStatusKey) {
  const color = status === 'Released' ? 'success' : 'default';
  return {
  text: SubmissionStatusEnum[status]?.title || status,
  color,
  };
}

// get all status transitions from the api
const allowedStatusTransitions = ref<AllowedStatusTransitions | null>(null);
  onMounted(async () => {
  allowedStatusTransitions.value = await getAllStatusTransitions();
});

function isReviewerForSubmission(): boolean {
  if (!currentUser.value?.orcid) {
    return false;
  }
  return store.submission.record!.reviewers.includes(currentUser.value.orcid);
}

function formatStatusTransitions(currentStatus: SubmissionStatusKey, dropdownType: SubmissionEditorRole | 'admin', transitions: AllowedStatusTransitions) {
  const excludeFromAll: SubmissionStatusKey[] = [
    'InProgress',
    'SubmittedPendingReview',
  ];

  // Admins can see all statuses and select any that aren't user invoked
  if (dropdownType === 'admin') {
    return (Object.keys(SubmissionStatusEnum) as SubmissionStatusKey[])
      .filter((key) => !excludeFromAll.includes(key) || key === currentStatus)
      .map((key) => ({
        value: key,
        title: SubmissionStatusEnum[key].title,
      }));
  }

  // Non-admins can only see and select allowed transitions
  const user_transitions = transitions[dropdownType] || {};
  const allowedStatusTransitions = user_transitions[currentStatus] || [];

  // Include the current status so it can be displayed
  const statusesToShow = [...allowedStatusTransitions];
  if (!statusesToShow.includes(currentStatus)) {
    statusesToShow.push(currentStatus);
  }

  // Return allowed transitions
  return (Object.keys(SubmissionStatusEnum) as SubmissionStatusKey[])
    .filter((key) => statusesToShow.includes(key as SubmissionStatusKey))
    .map((key) => ({
      value: key,
      title: SubmissionStatusEnum[key].title,
    }));
}

// get available transitions for an admin or a reviewer (depending on user) based on sample set's current status
function getFormattedStatusTransitions(item: SubmissionSampleSetListItem): StatusOption[] {
  if (!allowedStatusTransitions.value) {
    return [];
  }
  let dropdown_type: 'reviewer' | 'admin';
  if (currentUser.value?.is_admin) {
    dropdown_type = 'admin';
  } else if (isReviewerForSubmission()) {
    dropdown_type = 'reviewer';
  } else {
    return [];
  }
  return formatStatusTransitions(item.status as SubmissionStatusKey, dropdown_type, allowedStatusTransitions.value);
}

async function resume(item: SubmissionSampleSetListItem) {
  await store.loadSampleSet(item.id);
  router?.push({ name: 'Multiomics Form', params: { sampleSetId: item.id } });
}

function handleOpenDeleteDialog(item: SubmissionSampleSetListItem | null) {
  deleteDialogSubmission.value = item;
  if (deleteDialogSubmission.value) {
    isDeleteDialogOpen.value = true;
  }
}

async function handleDelete(item: SubmissionSampleSetListItem | null) {
  if (!item) {
    return;
  }
  await deleteSampleSet(item.id);
  sampleSet.value = await listSubmissionSampleSets(store.submission.record!.id);
  deleteDialogSubmission.value = null;
  isDeleteDialogOpen.value = false;
}

//function applySortOptions() {
//    const sortOrder = options.value.sortBy[0] ? options.value.sortBy[0].order : defaultSortOrder;
//    const sortBy = options.value.sortBy[0] ? options.value.sortBy[0].key : defaultSortBy;
//    //sampleSet.setSortOptions(sortBy, sortOrder);
//}

//function updateTableOptions(newOptions: any) {
//  options.value = newOptions;
//  applySortOptions();
//}

const statusUpdatingSubmissionId = ref<string | null>(null);
async function handleStatusChange(item: SubmissionSampleSetListItem, newStatus: string) {
  statusUpdatingSubmissionId.value = item.id;
  try {
    const patch: SubmissionSampleSetStatusPatch = {
      status: newStatus as SubmissionStatusKey,
    };
    await updateSubmissionSampleSetStatus(item.id, patch);
    sampleSet.value = await listSubmissionSampleSets(store.submission.record!.id);
  } finally {
    statusUpdatingSubmissionId.value = null;
  }
}

</script>
<template>
<PageSection>
  <v-card variant="outlined">
    <v-data-table-server
      :headers="headers"
      :items="sampleSet"
      :items-length="sampleSet.length"
      :items-per-page="itemsPerPage"
      :items-per-page-options="[10, 20, 50]"
    >
    <!-- removed @update:options="updateTableOptions" for now, until we know if we want pagination -->
      <template #[`item.name`]="{ item }">
        {{ item.name }}
      </template>

      <template #[`item.templates`]="{ item }">
        {{ Array.isArray(item.templates) ? item.templates.join(' + ') : item.templates }}
      </template>

      <template #[`item.status`]="{ item }">
          <div class="d-flex align-center">
            <v-select
              v-if="currentUser?.is_admin || isReviewerForSubmission()"
              :model-value="item.status"
              :items="getFormattedStatusTransitions(item)"
              :loading="statusUpdatingSubmissionId === item.id"
              density="compact"
              variant="underlined"
              hide-details
              :disabled="item.status === 'InProgress'"
              @update:model-value="(newStatus: string) => handleStatusChange(item, newStatus)"
            />
            <v-chip
              v-else
              :color="getStatus(item.status as SubmissionStatusKey).color"
            >
              {{ getStatus(item.status as SubmissionStatusKey).text }}
            </v-chip>
          </div>
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
            <span v-if="sampleSetEditableState[item.id] && isContributor">
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
            </v-list>
          </v-menu>
        </div>
      </template>
    </v-data-table-server>
  </v-card>
</PageSection>
<v-dialog
  v-model="isDeleteDialogOpen"
  :width="550"
>
  <v-card>
    <v-spacer />
    <v-card-title class="text-h5">
      Delete Sample Set
    </v-card-title>
    <v-card-text class="text-h5">
      <p v-if="deleteDialogSubmission && deleteDialogSubmission.name != ''">
        This will delete "{{ deleteDialogSubmission.name }}" and all associated data.
      </p>
      <p v-else>
        This will delete this sample set and all associated data, all other sample sets in this study will be unaffected.
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
</template>
