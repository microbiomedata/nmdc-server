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
import { stateRefs } from '@/store';

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
