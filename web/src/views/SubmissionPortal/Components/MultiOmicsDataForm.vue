<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import Definitions from '@/definitions';
import {
  multiOmicsForm, multiOmicsFormValid, multiOmicsAssociations, templateChoiceDisabled, contextForm,
} from '../store';

export default defineComponent({
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
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Multiomics Data
    </div>
    <div class="text-h5">
      Information about the type of samples being submitted.
    </div>
    <v-form
      ref="formRef"
      v-model="multiOmicsFormValid"
      class="my-6 mb-10"
      style="max-width: 1000px;"
    >
      <div v-if="contextForm.facilities.length === 0">
        <v-combobox
          v-model="multiOmicsForm.alternativeNames"
          label="Alternative Names"
          :hint="Definitions.studyAlternativeNames"
          persistent-hint
          deletable-chips
          multiple
          outlined
          chips
          small-chips
          dense
          append-icon=""
        />
        <v-text-field
          v-model="multiOmicsForm.GOLDStudyId"
          label="GOLD Study ID"
          :hint="Definitions.studyGoldID"
          persistent-hint
          outlined
          dense
        />
        <v-text-field
          v-model="multiOmicsForm.NCBIBioProjectId"
          label="NCBI BioProject Accession"
          :hint="Definitions.studyNCBIBioProjectAccession"
          persistent-hint
          outlined
          dense
        />
      </div>
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
        Data types cannot be changed when there are already metadata rows in step 5.  To change the template, return to step 5 and remove all data.
      </v-alert>

      <!-- JGI -->
      <div v-if="contextForm.facilities.includes('JGI')">
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
          :rules="[ v => !!v || 'JGI Study ID is required when processing was done at JGI' ]"
          label="JGI Study ID *"
          hint="JGI Study ID is required when processing was done at JGI"
          persistent-hint
          class="mt-4"
          outlined
          validate-on-blur
          dense
        />
      </div>

      <!-- EMSL -->
      <div v-if="contextForm.facilities.includes('EMSL')">
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
          :rules="[ v => !!v || 'EMSL Study Number is required when processing was done at EMSL' ]"
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
