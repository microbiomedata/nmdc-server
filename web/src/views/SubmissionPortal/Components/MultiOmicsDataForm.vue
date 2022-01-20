<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import {
  multiOmicsForm, multiOmicsFormValid, multiOmicsAssociations,
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
      /* functions */
      reValidate,
      /* Rules functions */
      // datasetDoiRules,
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
      style="max-width: 600px;"
    >
      <!-- DOI -->
      <v-checkbox
        v-model="multiOmicsAssociations.doi"
        label="Data has already been generated"
        hide-details
        class="mb-2 mt-0"
        @change="reValidate"
      />
      <v-text-field
        v-if="multiOmicsAssociations.doi"
        v-model="multiOmicsForm.datasetDoi"
        :rules="[ v => !!v || 'DOI is required when data has been generated already' ]"
        label="Dataset DOI (required)"
        validate-on-blur
        outlined
        dense
      />

      <!-- EMSL -->
      <v-checkbox
        v-model="multiOmicsAssociations.emsl"
        label="Study is associated with EMSL"
        hide-details
        class="mb-2 mt-0"
        @change="reValidate"
      />
      <v-text-field
        v-if="multiOmicsAssociations.emsl"
        v-model="multiOmicsForm.studyNumber"
        :rules="[ v => !!v || 'EMSL Study Number is required when associated' ]"
        label="EMSL Proposal / Study Number (required)"
        outlined
        validate-on-blur
        dense
      />

      <!-- JGI -->
      <v-checkbox
        v-model="multiOmicsAssociations.jgi"
        label="Study is associated with JGI"
        hide-details
        class="mb-2 mt-0"
      />
      <v-text-field
        v-if="multiOmicsAssociations.jgi"
        v-model="multiOmicsForm.JGIStudyId"
        :rules="[ v => !!v || 'JGI Study ID is required when associated' ]"
        label="JGI Study ID (required)"
        outlined
        validate-on-blur
        dense
      />
      <div
        v-else
        class="my-5"
      />

      <v-combobox
        v-model="multiOmicsForm.alternativeNames"
        label="Alternative Names"
        hint="Multiple values supported. Press enter key after each value."
        multiple
        outlined
        chips
        small-chips
        dense
      />
      <v-text-field
        v-model="multiOmicsForm.GOLDStudyId"
        label="GOLD Study ID"
        outlined
        dense
      />

      <v-text-field
        v-model="multiOmicsForm.NCBIBioProjectName"
        label="NCBI Bio Project Name"
        outlined
        dense
      />
      <v-textarea
        v-model="multiOmicsForm.NCBIBioProjectId"
        label="NCBI Bio Project ID"
        outlined
        dense
      />

      <p class="text-body-2 grey--text text--darken-2">
        Check all data types associated with this study
      </p>
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metagenome (JGI)"
        value="mg"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metatranscriptome (JGI)"
        value="mt"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metaproteome (EMSL)"
        value="mp"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metabolome (EMSL)"
        value="mb"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Natural Organic Matter (FT-ICR MS) (EMSL)"
        value="nom"
        hide-details
      />
    </v-form>
    <div class="d-flex">
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
        :disabled="!multiOmicsFormValid"
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
