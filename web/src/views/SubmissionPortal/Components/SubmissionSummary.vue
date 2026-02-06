<script lang="ts">
import { defineComponent, } from 'vue';
import {
  canEditSubmissionMetadata,
  createdDate,
  isTestSubmission,
  modifiedDate,
  statusDisplay,
  submissionPages,
  validationState,
} from '../store';
import PageTitle from '@/components/Presentation/PageTitle.vue';

export default defineComponent({
  components: { PageTitle },
  setup() {
    return {
      validationState,
      canEditSubmissionMetadata,
      submissionPages,
      createdDate,
      modifiedDate,
      statusDisplay,
      isTestSubmission,
    };
  },
});
</script>

<template>
  <div>
    <PageTitle
      title="Submission Summary"
    />

    <PageSection>
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
