<script lang="ts">
import {
  computed,
  defineComponent,
  ref,
} from 'vue';
import {
  validationState,
  canEditSubmissionMetadata,
  submissionPages,
  createdDate,
  modifiedDate,
  statusDisplay,
  isTestSubmission,
} from '../store';
import PageTitle from '@/components/Presentation/PageTitle.vue';

export default defineComponent({
  components: { PageTitle },
  setup() {
    const textVal = ref('');

    const panels = ref([]);

    const studyFormContent = computed(() => {
      if (validationState.studyForm?.length === 0) {
        return ['No changes needed.'];
      }
      return [...new Set(validationState.studyForm)];
    });

    const multiOmicsContent = computed(() => {
      if (validationState.multiOmicsForm?.length === 0) {
        return ['No changes needed.'];
      }
      return [...new Set(validationState.multiOmicsForm)];
    });

    const harmonizerContent = computed(() => {
      if (validationState.sampleEnvironmentForm) {
        return 'Validate and correct any errors in your harmonizer data.';
      }
      return 'You must select one or more templates in the sample environment tab.';
    });

    return {
      validationState,
      textVal,
      panels,
      studyFormContent,
      multiOmicsContent,
      harmonizerContent,
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

    <div class="d-flex my-4">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Submission Home' }"
      >
        <v-icon class="pl-1">
          mdi-arrow-left-circle
        </v-icon>
        Go to Submission List
      </v-btn>
    </div>
  </div>
</template>
