<script setup lang="ts">
import {
  author,
  createdDate,
  isTestSubmission,
  modifiedDate,
  statusDisplay,
  submissionPages,
} from '../store';
import { computed } from 'vue';
import { DataTableHeader } from 'vuetify';
import { stateRefs } from '@/store';

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

const submission = usePaginatedResults(ref([]), getSubmissions, ref([]), itemsPerPage);


// Check if the current logged-in user is also the author of the submission
const isCurrentUserAuthor = computed(() => {
  return stateRefs.user.value && stateRefs.user.value.orcid === author.value?.orcid;
});
</script>

<template>
  <div>
    <PageTitle
      title="Submission Summary"
    />

    <PageSection>
      <AttributeRow label="Submission Author">
        <div v-if="author">
          <span v-if="author.name">
            {{ author.name }}
          </span>
          <span v-else>
            {{ author.orcid }}
          </span>
          <span v-if="author.email">
            ({{ author.email }})
          </span>
          <span v-else>
            (<i class="text-disabled font-italic">No email address</i>)
          </span>
        </div>
        <div
          v-if="isCurrentUserAuthor"
          class="text-caption mt-1"
        >
          This is the email we will use to get in touch if we have questions. If it does not look correct, visit your
          <!-- eslint-disable-next-line -->
          <router-link :to="{ name: 'User' }">user profile</router-link>
          to update it.
        </div>
      </AttributeRow>
      <AttributeRow label="Created">
        {{ createdDate?.toLocaleString() }}
      </AttributeRow>
      <AttributeRow label="Last Modified">
        {{ modifiedDate?.toLocaleString() }}
      </AttributeRow>
      <AttributeRow label="Status">
        {{ statusDisplay }}
      </AttributeRow>
      <AttributeRow
        v-if="isTestSubmission"
        label="Is Test Submission?"
      >
        Yes
      </AttributeRow>
    </PageSection>

    <PageSection>
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
          <template #[`item.templates`]="{ item }">
            {{ item.templates.map((template) => HARMONIZER_TEMPLATES[template]?.displayName).join(' + ') }}
          </template>
          <template #[`item.date_last_modified`]="{ item }">
            {{ new Date(item.date_last_modified + 'Z').toLocaleString() }}
          </template>
          <template #[`header.status`]="{ column, getSortIcon, toggleSort }">
            <div class="d-flex align-center ga-1">
              <v-tooltip
                v-if="currentUser?.is_admin || (currentUser?.orcid && submission.data.results.results.some(item => item.reviewers.includes(currentUser!.orcid)))"
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
                <span>Reviewer can change status of assigned submissions. Some values are user-triggered statuses and cannot be changed or selected.</span>
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
                v-if="currentUser?.is_admin || isReviewerForSubmission(item)"
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
                <span v-if="editableByStatus(item.status) && isAnyContributorForSubmission(item)">
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
    </PageSection>

    <PageSection>
      <v-list class="pa-0 border rounded">
        <template
          v-for="(page, index) in submissionPages"
          :key="page.title"
        >
          <v-divider v-if="index > 0" />
          <v-list-item
            :to="page.link"
            link
            :title="page.title"
          >
            <template #append>
              <v-icon>
                mdi-chevron-right
              </v-icon>
            </template>
          </v-list-item>
        </template>
      </v-list>
    </PageSection>
  </div>
</template>
