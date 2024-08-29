<script lang="ts">
import { defineComponent, computed } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';
import {
  templateChoiceDisabled,
  templateList,
  packageName,
  canEditSubmissionMetadata,
} from '../store';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';

export default defineComponent({
  components: { SubmissionDocsLink, SubmissionPermissionBanner },
  setup() {
    const templateListDisplayNames = computed(() => templateList.value
      .map((templateKey) => HARMONIZER_TEMPLATES[templateKey].displayName)
      .join(' + '));

    return {
      packageName,
      HARMONIZER_TEMPLATES,
      templates: Object.entries(HARMONIZER_TEMPLATES),
      templateListDisplayNames,
      templateChoiceDisabled,
      canEditSubmissionMetadata,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Environment Package
      <submission-docs-link anchor="environmental-package" />
    </div>
    <div class="text-h5">
      Choose environment package for your data.
    </div>
    <submission-permission-banner
      v-if="!canEditSubmissionMetadata()"
    />

    <v-checkbox
      v-for="option in templates.filter((v) => v[1].status === 'published')"
      :key="option[0]"
      v-model="packageName"
      dense
      hide-details
      class="my-6"
      :disabled="templateChoiceDisabled && !canEditSubmissionMetadata()"
      :label="HARMONIZER_TEMPLATES[option[0]].displayName"
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
      :label="HARMONIZER_TEMPLATES[option[0]].displayName"
      :value="option[0]"
    />
    <v-alert
      v-if="!templateChoiceDisabled"
      color="grey lighten-2"
    >
      <p class="text-h5">
        DataHarmonizer Template Choice
      </p>
      Your DataHarmonizer template is "{{ templateListDisplayNames }}".
    </v-alert>
    <v-alert
      v-else
      type="warning"
    >
      <p class="text-h5">
        Template choice disabled
      </p>
      Your DataHarmonizer template is "{{ templateListDisplayNames }}".
      Template cannot be changed when there are already metadata rows in step 6.
      To change the template, return to step 6 and remove all data.
    </v-alert>
    <div class="d-flex">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Multiomics Form' }"
      >
        <v-icon class="pr-1">
          mdi-arrow-left-circle
        </v-icon>
        Go to previous step
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        depressed
        :disabled="!packageName"
        :to="{
          name: 'Submission Sample Editor',
        }"
      >
        <v-icon class="pr-1">
          mdi-arrow-right-circle
        </v-icon>
        Go to next step
      </v-btn>
    </div>
  </div>
</template>
