<script setup lang="ts">
import { computed, useTemplateRef } from 'vue';
import { HARMONIZER_TEMPLATES, TemplateName } from '@/views/SubmissionPortal/types';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import PageTitle from '@/components/Presentation/PageTitle.vue';
import SubmissionForm from '@/views/SubmissionPortal/Components/SubmissionForm.vue';
import SubmissionUneditableBanner from '@/views/SubmissionPortal/Components/SubmissionUneditableBanner.vue';
import { useSubmissionStore } from '../store';

const store = useSubmissionStore();
const { templateHasData } = store;
const sampleEnvironmentForm = computed(() => store.sampleSet.forms.sampleEnvironmentForm);

const templates = Object.entries(HARMONIZER_TEMPLATES);

const formRef = useTemplateRef<InstanceType<typeof SubmissionForm>>('formRef');
const templateListDisplayNames = computed(() => store.templateList
  .map((templateKey) => HARMONIZER_TEMPLATES[templateKey].displayName)
  .join(' + '));
</script>

<template>
  <div>
    <SubmissionUneditableBanner
      :allowed-roles="['owner', 'editor']"
      in-sample-set-context
      edge-to-edge
    />
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
      in-sample-set-context
      @valid-state-changed="(state) => sampleEnvironmentForm.validation = state"
    >
      <v-input
        :model-value="sampleEnvironmentForm.packageName"
        validate-on="input eager"
        :rules="[(v) => (!!v && v.length > 0) || 'Please select at least one template.']"
      >
        <template #default>
          <fieldset class="border-0">
            <v-checkbox
              v-for="option in templates.filter((v) => v[1].status === 'published')"
              :key="option[0]"
              v-model="sampleEnvironmentForm.packageName"
              hide-details
              :disabled="templateHasData(option[0] as TemplateName) || formRef?.isDisabled"
              :label="HARMONIZER_TEMPLATES[option[0] as TemplateName]?.displayName"
              :value="option[0]"
            />
          </fieldset>
        </template>
      </v-input>
    </SubmissionForm>
    <template v-if="formRef && !formRef.isDisabled">
      <v-alert
        v-if="!templateHasData('ANY')"
        color="grey lighten-2"
        class="my-3"
      >
        <p class="text-h5">
          Sample Metadata Template Choice
        </p>
        <template
          v-if="sampleEnvironmentForm.packageName.length!=0"
        >
          Your Sample Metadata template is "{{ templateListDisplayNames }}".
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
        Your Sample Metadata template is "{{ templateListDisplayNames }}".
        Template choices cannot be disabled while the matching tab in Sample Metadata has data present.
        To disable the template, return to Sample Metadata and remove all data from that tab. You may add new templates at any time.
      </v-alert>
    </template>
    <v-alert
      v-if="formRef?.isDisabled && sampleEnvironmentForm.packageName.length > 0"
      color="grey lighten-2"
      class="my-3"
    >
      <p class="text-h5">
        Sample Metadata Template
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
