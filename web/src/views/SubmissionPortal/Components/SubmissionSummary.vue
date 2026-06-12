<script setup lang="ts">
import { useSubmissionStore } from '../store';
import { computed } from 'vue';
import { stateRefs } from '@/store';

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
</template>
