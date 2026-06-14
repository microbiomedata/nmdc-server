<script lang="ts">
import { computed, defineComponent, useTemplateRef } from 'vue';
import { HARMONIZER_TEMPLATES } from '@/views/SubmissionPortal/types';
import {
  multiOmicsForm,
  sampleEnvironmentForm,
  templateHasData,
  templateList,
} from '../store';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import PageTitle from '@/components/Presentation/PageTitle.vue';
import SubmissionForm from '@/views/SubmissionPortal/Components/SubmissionForm.vue';

export default defineComponent({
  components: { SubmissionForm, SubmissionDocsLink, PageTitle },
  setup() {
    const formRef = useTemplateRef<InstanceType<typeof SubmissionForm>>('formRef');
    const templateListDisplayNames = computed(() => templateList.value
      .map((templateKey) => HARMONIZER_TEMPLATES[templateKey]?.displayName)
      .join(' + '));

    const checkboxDisabledReason = computed<Record<string, string | null>>(() => {
      const notes: Record<string, string | null> = {};
      Object.entries(HARMONIZER_TEMPLATES).forEach(([key, template]) => {
        if (templateHasData(template.sampleDataSlot)) {
          notes[key] = 'This template cannot be deselected because there is data present in the Sample Metadata tab for this template.';
        } else if (key === 'isolate' && (
          multiOmicsForm.omicsProcessingTypes.includes('isolate-genome') ||
          multiOmicsForm.omicsProcessingTypes.includes('isolate-transcriptome') ||
          multiOmicsForm.omicsProcessingTypes.includes('isolate-genome-jgi') ||
          multiOmicsForm.omicsProcessingTypes.includes('isolate-transcriptome-jgi')
        )) {
          notes[key] = 'This template cannot be deselected because an isolate omics processing type is selected on the Multi-omics Data page.';
        } else {
          notes[key] = null;
        }
      });
      return notes;
    });

    return {
      checkboxDisabledReason,
      sampleEnvironmentForm,
      formRef,
      HARMONIZER_TEMPLATES,
      templates: Object.entries(HARMONIZER_TEMPLATES),
      templateListDisplayNames,
      templateHasData,
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
        for your samples. If isolation was performed, select the "isolate" option. If isolates were obtained from a
        provider, select only the "isolate" option.
      </template>
    </PageTitle>
    <SubmissionForm
      @valid-state-changed="(state) => sampleEnvironmentForm.validation = state"
    >
      <v-input
        :model-value="sampleEnvironmentForm.packageName"
        validate-on="input eager"
        :rules="[(v) => (!!v && v.length > 0) || 'Please select at least one template.']"
      >
        <template #default>
          <fieldset class="border-0">
            <template
              v-for="option in templates.filter((v) => v[1].status === 'published')"
              :key="option[0]"
            >
              <v-checkbox
                v-model="sampleEnvironmentForm.packageName"
                hide-details
                :disabled="formRef?.isDisabled || checkboxDisabledReason[option[0]] !== null"
                :label="HARMONIZER_TEMPLATES[option[0]]?.displayName"
                :value="option[0]"
              />
              <div
                v-if="checkboxDisabledReason[option[0]]"
                class="ml-8 text-caption"
              >
                {{ checkboxDisabledReason[option[0]] }}
              </div>
            </template>
          </fieldset>
        </template>
      </v-input>
    </SubmissionForm>
    <template v-if="formRef && !formRef.isDisabled">
      <v-alert
        v-if="!templateHasData('all')"
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
