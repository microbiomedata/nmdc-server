<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import Definitions from '@/definitions';
import {
  multiOmicsForm, multiOmicsFormValid, multiOmicsAssociations, templateChoiceDisabled, contextForm, canEditSubmissionMetadata,
} from '../store';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';

export default defineComponent({
  components: { SubmissionDocsLink, SubmissionPermissionBanner },
  setup() {
    const formRef = ref();

    function reValidate() {
      formRef.value.validate();
    }

    return {
      formRef,
      multiOmicsForm,
      multiOmicsAssociations,
      multiOmicsFormValid,
      Definitions,
      templateChoiceDisabled,
      contextForm,
      /* functions */
      reValidate,
      canEditSubmissionMetadata,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Multi-omics Data
      <submission-docs-link anchor="multi-omics-data" />
    </div>
    <div class="text-h5">
      Information about the type of samples being submitted.
    </div>
    <submission-permission-banner
      v-if="!canEditSubmissionMetadata()"
    />
    <v-form
      ref="formRef"
      v-model="multiOmicsFormValid"
      class="my-6 mb-10"
      style="max-width: 1000px;"
      :disabled="!canEditSubmissionMetadata()"
    >
      <div class="text-h4">
        Data types *
      </div>
      <div class="text-body-2 grey--text text--darken-2 mb-4">
        {{ Definitions.metadataTypes }}
      </div>

      <v-alert
        v-if="templateChoiceDisabled"
        type="warning"
      >
        <p class="text-h5">
          Data type choice disabled
        </p>
        Data types cannot be changed when there are already metadata rows in step 6.  To change the template, return to step 6 and remove all data.
      </v-alert>

      <!-- JGI -->
      <div v-if="contextForm.facilities.includes('JGI') || contextForm.facilityGenerated === true">
        <div class="text-h6">
          Joint Genome Institute (JGI)
        </div>
        <v-checkbox
          v-model="multiOmicsForm.omicsProcessingTypes"
          label="Metagenome"
          value="mg-jgi"
          :disabled="templateChoiceDisabled"
          hide-details
        />
        <v-checkbox
          v-model="multiOmicsForm.omicsProcessingTypes"
          label="Metagenome (Long Read)"
          value="mg-lr-jgi"
          :disabled="templateChoiceDisabled"
          hide-details
        />
        <v-checkbox
          v-model="multiOmicsForm.omicsProcessingTypes"
          label="Metatranscriptome"
          value="mt-jgi"
          :disabled="templateChoiceDisabled"
          hide-details
        />
        <v-checkbox
          v-model="multiOmicsForm.omicsProcessingTypes"
          label="Metabolome"
          value="mb-jgi"
          disabled
          hide-details
        />
        <v-text-field
          v-if="multiOmicsForm.omicsProcessingTypes.some((v) => v.endsWith('jgi'))"
          v-model="multiOmicsForm.JGIStudyId"
          :rules="[
            v => !!v || 'JGI Proposal ID/Study ID is required when processing was done at JGI' ,
            v => /^\d{6}$/.test(v) || 'JGI Proposal ID/Study ID must be a 6 digit numerical value'
          ]"
          label="JGI Proposal ID/Study ID *"
          hint="This is the 6 digit ID assigned to your JGI Proposal and is required when completing metadata for samples to be sent to JGI for sequencing."
          persistent-hint
          class="mt-4"
          outlined
          validate-on-blur
          dense
        />
      </div>

      <!-- EMSL -->
      <div v-if="contextForm.facilities.includes('EMSL') || contextForm.facilityGenerated === true">
        <div class="text-h6 mt-4">
          Environmental Molecular Science Laboratory (EMSL)
        </div>
        <v-checkbox
          v-model="multiOmicsForm.omicsProcessingTypes"
          label="Metaproteome"
          value="mp-emsl"
          :disabled="templateChoiceDisabled"
          hide-details
        />
        <v-checkbox
          v-model="multiOmicsForm.omicsProcessingTypes"
          label="Metabolome"
          value="mb-emsl"
          :disabled="templateChoiceDisabled"
          hide-details
        />
        <v-checkbox
          v-model="multiOmicsForm.omicsProcessingTypes"
          label="Natural Organic Matter (FT-ICR MS)"
          value="nom-emsl"
          :disabled="templateChoiceDisabled"
          hide-details
        />
        <v-text-field
          v-if="multiOmicsForm.omicsProcessingTypes.some((v) => v.endsWith('emsl'))"
          v-model="multiOmicsForm.studyNumber"
          :rules="[
            v => !!v || 'EMSL Study Number is required when processing was done at EMSL',
            v => /^\d{5}$/.test(v) || 'EMSL Study Number must be a 5 digit numerical value'
          ]"
          hint="EMSL Study Number is required when processing was done at EMSL"
          persistent-hint
          label="EMSL Proposal / Study Number *"
          class="mt-4"
          outlined
          validate-on-blur
          dense
        />
      </div>
      <!-- Other -->
      <div class="text-h6 mt-4">
        Other Non-DOE
      </div>
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metagenome"
        value="mg"
        :disabled="templateChoiceDisabled"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metatranscriptome"
        value="mt"
        :disabled="templateChoiceDisabled"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metaproteome"
        value="mp"
        :disabled="templateChoiceDisabled"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metabolome"
        value="mb"
        :disabled="templateChoiceDisabled"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Natural Organic Matter (FT-ICR MS)"
        value="nom"
        :disabled="templateChoiceDisabled"
        hide-details
      />
    </v-form>
    <strong>* indicates required field</strong>
    <div class="d-flex mt-5">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Study Form' }"
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
        :disabled="(!multiOmicsFormValid)"
        :to="{ name: 'Environment Package' }"
      >
        Go to next step
        <v-icon class="pl-1">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
  </div>
</template>
