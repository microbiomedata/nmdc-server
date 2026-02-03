<script lang="ts">
import { computed, defineComponent } from 'vue';
import { HARMONIZER_TEMPLATES } from '@/views/SubmissionPortal/types';
import {
  canEditSubmissionByStatus,
  canEditSubmissionMetadata,
  packageName,
  status,
  templateHasData,
  templateList,
  validationState,
} from '../store';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';
import StatusAlert from './StatusAlert.vue';
import PageTitle from '@/components/Presentation/PageTitle.vue';
import SubmissionForm from '@/views/SubmissionPortal/Components/SubmissionForm.vue';

export default defineComponent({
  components: { SubmissionForm, SubmissionDocsLink, SubmissionPermissionBanner, StatusAlert, PageTitle },
  setup() {
    const templateListDisplayNames = computed(() => templateList.value
      .map((templateKey) => HARMONIZER_TEMPLATES[templateKey]?.displayName)
      .join(' + '));

    return {
      packageName,
      HARMONIZER_TEMPLATES,
      templates: Object.entries(HARMONIZER_TEMPLATES),
      templateListDisplayNames,
      canEditSubmissionMetadata,
      templateHasData,
      canEditSubmissionByStatus,
      status,
      StatusAlert,
      validationState,
    };
  },
});
</script>

<template>
  <div>
    <PageTitle
      title="Sample Environment"
    >
      <template #help>
        <submission-docs-link anchor="environmental-package" />
      </template>
      <template #subtitle>
        Choose the
        <a
          href="https://genomicsstandardsconsortium.github.io/mixs/#extensions"
          target="_blank"
          rel="noopener noreferrer"
        >MIxS Extension</a>
        for your samples.
      </template>
    </PageTitle>
    <SubmissionForm
      @valid-state-changed="(state) => validationState.sampleEnvironmentForm = state"
    >
      <v-input
        v-model="packageName"
        validate-on="input eager"
        :rules="[(v) => (!!v && v.length > 0) || 'Please select at least one template.']"
      >
        <template #default>
          <fieldset class="border-0">
            <v-checkbox
              v-for="option in templates.filter((v) => v[1].status === 'published')"
              :key="option[0]"
              v-model="packageName"
              hide-details
              :disabled="templateHasData(HARMONIZER_TEMPLATES[option[0]]?.sampleDataSlot) || !canEditSubmissionMetadata()"
              :label="HARMONIZER_TEMPLATES[option[0]]?.displayName"
              :value="option[0]"
            />
          </fieldset>
        </template>
      </v-input>
    </SubmissionForm>
    <template v-if="canEditSubmissionByStatus()">
      <v-alert
        v-if="!templateHasData('all')"
        color="grey lighten-2"
        class="my-3"
      >
        <p class="text-h5">
          DataHarmonizer Template Choice
        </p>
        <template
          v-if="packageName.length!=0"
        >
          Your DataHarmonizer template is "{{ templateListDisplayNames }}".
        </template>
        <template
          v-else
        >
          Please Select One or More Options for Your Template.
        </template>
      </v-alert>
      <v-alert
        v-else
        type="warning"
        class="mb-4"
      >
        <p class="text-h5">
          Template choice disabled
        </p>
        Your DataHarmonizer template is "{{ templateListDisplayNames }}".
        Template choices cannot be disabled while the matching tab in step 5 has data present.
        To disable the template, return to step 5 and remove all data from that tab. You may add new templates at any time.
      </v-alert>
    </template>
    <v-alert
      v-if="!canEditSubmissionByStatus() && packageName.length > 0"
      color="grey lighten-2"
      class="my-3"
    >
      <p class="text-h5">
        DataHarmonizer Template
      </p>
      This submission uses the "{{ templateListDisplayNames }}" template.
    </v-alert>
    <div class="d-flex">
      <v-btn-grey :to="{ name: 'Multiomics Form' }">
        <v-icon class="pr-2">
          mdi-arrow-left-circle
        </v-icon>
        Go to Multiomics Form
      </v-btn-grey>
      <v-spacer />
      <v-btn
        color="primary"
        :to="{
          name: 'Submission Sample Editor',
        }"
      >
        Go to Sample Metadata
        <v-icon class="pl-2">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
  </div>
</template>
