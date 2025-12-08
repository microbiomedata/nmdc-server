<script lang="ts">
import { defineComponent, computed, watch } from 'vue';
import { HARMONIZER_TEMPLATES } from '@/views/SubmissionPortal/types';
import {
  templateList,
  packageName,
  canEditSubmissionMetadata,
  templateHasData,
  canEditSubmissionByStatus,
  SubmissionStatusTitleMapping,
  status,
  validForms,
} from '../store';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';
import StatusAlert from './StatusAlert.vue';

export default defineComponent({
  components: { SubmissionDocsLink, SubmissionPermissionBanner, StatusAlert },
  setup() {
    const templateListDisplayNames = computed(() => templateList.value
      .map((templateKey) => HARMONIZER_TEMPLATES[templateKey]?.displayName)
      .join(' + '));

    watch(packageName, () => {
      if (packageName.value.length === 0) {
        validForms.templatesValid = false;
      } else {
        validForms.templatesValid = true;
      }
    });

    return {
      packageName,
      HARMONIZER_TEMPLATES,
      templates: Object.entries(HARMONIZER_TEMPLATES),
      templateListDisplayNames,
      canEditSubmissionMetadata,
      templateHasData,
      canEditSubmissionByStatus,
      SubmissionStatusTitleMapping,
      status,
      StatusAlert,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Sample Environment
      <submission-docs-link anchor="environmental-package" />
    </div>
    <div class="text-h5">
      Choose the
      <a
        href="https://genomicsstandardsconsortium.github.io/mixs/#extensions"
        target="_blank"
        rel="noopener noreferrer"
      >MIxS Extension</a>
      for your samples.
    </div>
    <submission-permission-banner
      v-if="canEditSubmissionByStatus() && !canEditSubmissionMetadata()"
    />
    <StatusAlert v-if="!canEditSubmissionByStatus()" />
    <v-checkbox
      v-for="option in templates.filter((v) => v[1].status === 'published')"
      :key="option[0]"
      v-model="packageName"
      dense
      hide-details
      :disabled="templateHasData(HARMONIZER_TEMPLATES[option[0]]?.sampleDataSlot) || !canEditSubmissionMetadata()"
      :label="HARMONIZER_TEMPLATES[option[0]]?.displayName"
      :value="option[0]"
    />
    <p class="grey--text text--darken-1 my-5">
      Under development
    </p>
    <v-checkbox
      v-for="option in templates.filter((v) => v[1].status === 'disabled')"
      :key="option[0]"
      v-model="packageName"
      hide-details
      :disabled="true"
      :label="HARMONIZER_TEMPLATES[option[0]]?.displayName"
      :value="option[0]"
    />
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
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Multiomics Form' }"
      >
        <v-icon class="pr-2">
          mdi-arrow-left-circle
        </v-icon>
        Go to Multiomics Form
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        depressed
        :to="{
          name: 'Submission Sample Editor',
        }"
      >
        Go to Data Harmonizer
        <v-icon class="pl-2">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
  </div>
</template>
