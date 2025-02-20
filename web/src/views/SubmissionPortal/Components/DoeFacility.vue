<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import {
  multiOmicsForm, templateChoiceDisabled, contextForm,
} from '../store';

export default defineComponent({
  props: {
    label: {
      type: String,
      default: 'Data generated ',
    },
  },
  setup() {
    return {
      multiOmicsForm,
      contextForm,
      templateChoiceDisabled,
    };
  },

});
</script>

<template>
  <div>
    <legend
      class="v-label theme--light mb-2"
      style="font-size: 14px;"
    >
      Which facility?
    </legend>
    <v-checkbox
      v-model="contextForm.facilities"
      label="EMSL"
      value="EMSL"
      hide-details
      class="mb-2 mt-0"
    />
    <div
      v-if="contextForm.facilities.includes('EMSL')"
      class="my-4 ml-4"
    >
      <div
        class="v-label theme--light"
        style="font-size: 14px;"
      >
        Data types?
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
    <v-checkbox
      v-model="contextForm.facilities"
      label="JGI"
      value="JGI"
      hide-details
      class="mb-2 mt-0"
    />
    <!-- JGI -->
    <div
      v-if="contextForm.facilities.includes('JGI')"
      class="my-4 ml-4"
    >
      <div
        class="v-label theme--light mb-2"
        style="font-size: 14px;"
      >
        Data types?
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
          v => !!v || 'JGI Proposal ID/Study ID is required when processing was done at JGI',
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
  </div>
</template>
