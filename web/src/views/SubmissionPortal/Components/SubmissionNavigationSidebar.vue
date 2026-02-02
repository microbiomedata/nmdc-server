<script lang="ts">
import { computed, defineComponent, } from 'vue';
import { studyForm, validationState } from '../store';
import { SampleMetadataValidationState } from '@/views/SubmissionPortal/types.ts';

export default defineComponent({
  setup() {
    function combineErrors(...errorLists: (null | string[])[]) : null | string[] {
      let combined: null | string[] = null;
      errorLists.forEach((errors) => {
        if (errors) {
          if (combined === null) {
            combined = [];
          }
          combined = combined.concat(errors);
        }
      });
      return combined;
    }

    function combineSampleMetadataErrors(sampleMetadataState: SampleMetadataValidationState | null) : string[] | null {
      if (sampleMetadataState === null) {
        return null;
      }
      const combinedErrors: string[] = [];
      Object.keys(sampleMetadataState.tabsValidated).forEach((tab) => {
        let message = '';
        if (!sampleMetadataState.tabsValidated[tab]) {
          message = `Tab "${tab}" has not been validated.`;
        }
        if (tab in sampleMetadataState.invalidCells) {
          const invalidCells = sampleMetadataState.invalidCells[tab];
          if (invalidCells && Object.keys(invalidCells).length > 0) {
            message = `Tab "${tab}" has invalid cells.`;
          }
        }
        if (message) {
          combinedErrors.push(message);
        }
      })
      return combinedErrors;
    }

    const pages = computed<{
      title: string;
      pageName: string;
      valid?: null | string[];
    }[]>(() => [
      {
        title: 'Submission Summary',
        pageName: 'Submission Summary',
      },
      {
        title: 'Study Form',
        pageName: 'Study Form',
        valid: validationState.studyForm,
      },
      {
        title: 'Multiomics Form',
        pageName: 'Multiomics Form',
        valid: combineErrors(validationState.multiOmicsForm, validationState.senderShippingInfoForm),
      },
      {
        title: 'Sample Environment',
        pageName: 'Sample Environment',
        valid: validationState.sampleEnvironmentForm,
      },
      {
        title: 'Data Harmonizer',
        pageName: 'Submission Sample Editor',
        valid: combineSampleMetadataErrors(validationState.sampleMetadata),
      },
    ]);

    return {
      pages,
      studyForm
    };
  },
});
</script>

<template>
  <v-navigation-drawer
    app
    permanent
    clipped
  >
    <v-list-item subtitle="Click to go to">
      <template #title>
        <div class="text-h6 text-wrap">
          {{ studyForm.studyName }}
        </div>
      </template>
    </v-list-item>

    <v-divider />

    <v-list
      dense
      nav
    >
      <v-list-item
        v-for="page in pages"
        :key="page.pageName"
        :to="{name: page.pageName}"
        link
        :title="page.title"
      >
        <template
          v-if="Array.isArray(page.valid)"
          #append
        >
          <v-badge
            v-if="page.valid?.length != 0"
            inline
            color="red"
            :content="page.valid?.length"
            :title="page.valid.join('\n')"
          />
          <v-icon
            v-else
            color="green"
          >
            mdi-check-circle-outline
          </v-icon>
        </template>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>
