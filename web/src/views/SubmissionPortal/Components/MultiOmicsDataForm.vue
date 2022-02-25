<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import Definitions from '@/definitions';
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
      Definitions,
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
      style="max-width: 1000px;"
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
        :hint="Definitions.doi"
        persistent-hint
        label="Dataset DOI *"
        validate-on-blur
        outlined
        dense
      />
      <div
        v-else
        class="my-5"
      />

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
        v-model="multiOmicsForm.NCBIBioProjectName"
        label="NCBI BioProject Title"
        :hint="Definitions.studyNCBIProjectTitle"
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

      <div class="text-h4">
        Data types *
      </div>
      <div class="text-body-2 grey--text text--darken-2 mb-4">
        {{ Definitions.metadataTypes }}
      </div>

      <!-- JGI -->
      <div class="text-h6">
        Joint Genome Institute (JGI)
      </div>
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metagenome"
        value="mg-jgi"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metatranscriptome"
        value="mt-jgi"
        disabled
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

      <!-- EMSL -->
      <div class="text-h6 mt-4">
        Environmental Molecular Science Laboratory (EMSL)
      </div>
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metaproteome"
        value="mp-emsl"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metabolome"
        value="mb-emsl"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Natural Organic Matter (FT-ICR MS)"
        value="nom-emsl"
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

      <!-- Other -->
      <div class="text-h6 mt-4">
        Other Non-DOE
      </div>
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metagenome"
        value="mg"
        disabled
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metatranscriptome"
        value="mt"
        disabled
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metaproteome"
        value="mp"
        disabled
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metabolome"
        value="mb"
        disabled
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Natural Organic Matter (FT-ICR MS)"
        value="nom"
        disabled
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
