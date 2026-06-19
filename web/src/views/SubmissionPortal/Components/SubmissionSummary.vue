<script setup lang="ts">
import { useSubmissionStore } from '../store';
import { computed } from 'vue';
import { stateRefs } from '@/store';
import SampleSetTable from './SampleSetTable.vue';

const store = useSubmissionStore();

const author = computed(() => store.submission.record?.author);
const createdDate = computed(
  () => store.submission.record?.created ? new Date(store.submission.record.created + 'Z') : null
);
const modifiedDate = computed(
  () => store.submission.record?.date_last_modified ? new Date(store.submission.record.date_last_modified + 'Z') : null
);

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
      <AttributeRow
        v-if="store.submission.record?.is_test_submission"
        label="Is Test Submission?"
      >
        Yes
      </AttributeRow>
    </PageSection>
  </div>
  <PageSection
    heading="Study Information"
    subheading="Use this form to enter information about the research initiative as a whole and the people contributing to it. Each NMDC Submission corresponds to one research initiative."
  >
    <v-list class="pa-0 border rounded">
      <v-list-item
        :to="{ name: 'Study Form' }"
        link
        class="w-100"
      >
        <v-list-item-title class="text-body-1 font-weight-medium">
          Study Information
        </v-list-item-title>
        <template #append>
          <v-icon>mdi-chevron-right</v-icon>
        </template>
      </v-list-item>
    </v-list>
  </PageSection>
  <PageSection
    heading="Sample Sets"
    subheading="TODO add explainer text"
  >
    <v-card-text>
      <v-btn
        color="primary"
        :to="{ name: 'Create Sample Set' }"
      >
        <v-icon>mdi-plus</v-icon>
        Create Sample Set
      </v-btn>
    </v-card-text>
    <SampleSetTable/>
  </PageSection>
</template>
