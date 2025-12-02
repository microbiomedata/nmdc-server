<script lang="ts">
import { defineComponent } from 'vue';
import { HARMONIZER_TEMPLATES } from '@/views/SubmissionPortal/types';
import Definitions from '@/definitions';
import {
  multiOmicsForm, addAwardDoi, templateHasData, checkJGITemplates,
} from '../store';
import SubmissionContextShippingForm from './SubmissionContextShippingForm.vue';

export default defineComponent({
  components: {
    SubmissionContextShippingForm,

  },
  props: {
    label: {
      type: String,
      default: 'Data generated ',
    },
  },
  emits: ['revalidate'],

  setup(_, { emit }) {
    function facilityChange() {
      if (multiOmicsForm.awardDois === null || multiOmicsForm.awardDois.length < multiOmicsForm.facilities.length) {
        addAwardDoi();
      }
      emit('revalidate');
    }

    return {
      facilityChange,
      Definitions,
      multiOmicsForm,
      templateHasData,
      checkJGITemplates,
      HARMONIZER_TEMPLATES,
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
      v-model="multiOmicsForm.facilities"
      label="EMSL"
      value="EMSL"
      hide-details
      :disabled="templateHasData(HARMONIZER_TEMPLATES.emsl?.sampleDataSlot) || undefined"
      @change="facilityChange"
    />
    <div
      v-if="multiOmicsForm.facilities.includes('EMSL')"
      class="mb-4 ml-4"
    >
      <div class="d-flex flex-column grow">
        <v-text-field
          v-if="multiOmicsForm.facilities.includes('EMSL')"
          v-model="multiOmicsForm.studyNumber"
          :rules="[
            v => !!v || 'EMSL Proposal Number is required when processing was done at EMSL',
            v => /^\d{5}$/.test(v) || 'EMSL Proposal Number must be a 5 digit numerical value'
          ]"
          hint="EMSL Proposal Number is required when processing was done at EMSL"
          persistent-hint
          label="EMSL Proposal Number *"
          class="mt-4"
          variant="outlined"
          validate-on-blur
        />
      </div>
      <v-radio-group
        v-if="multiOmicsForm.dataGenerated === false && multiOmicsForm.facilities.includes('EMSL')"
        v-model="multiOmicsForm.ship"
        label="Will samples be shipped? *"
        :rules="[v => (v === true || v === false) || 'This field is required']"
        @change="$emit('revalidate')"
      >
        <v-radio
          label="No"
          :value="false"
        />
        <v-radio
          label="Yes"
          :value="true"
        />
      </v-radio-group>
      <submission-context-shipping-form
        v-if="multiOmicsForm.dataGenerated === false && multiOmicsForm.ship && multiOmicsForm.facilities.includes('EMSL')"
      />
      <div
        class="v-label theme--light mb-2"
        style="font-size: 14px;"
      >
        Data types?
      </div>

      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Lipidome"
        value="lipidome-emsl"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.emsl?.sampleDataSlot) || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metaproteome"
        value="mp-emsl"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.emsl?.sampleDataSlot) || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metabolome"
        value="mb-emsl"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.emsl?.sampleDataSlot) || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Natural Organic Matter (FT-ICR MS)"
        value="nom-emsl"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.emsl?.sampleDataSlot) || undefined"
        hide-details
      />
    </div>
    <v-checkbox
      v-model="multiOmicsForm.facilities"
      label="JGI"
      value="JGI"
      hide-details
      :disabled="checkJGITemplates() || undefined"
      @change="facilityChange"
    />
    <div
      v-if="multiOmicsForm.facilities.includes('JGI')"
      class="mb-4 ml-4"
    >
      <div class="d-flex flex-column grow">
        <v-text-field
          v-if="multiOmicsForm.facilities.includes('JGI')"
          v-model="multiOmicsForm.JGIStudyId"
          :rules="[
            v => !!v || 'JGI Proposal Number is required when processing was done at JGI',
            v => /^\d{6}$/.test(v) || 'JGI Proposal ID must be a 6 digit numerical value'
          ]"
          hint="JGI Proposal Number is required when processing was done at JGI"
          persistent-hint
          label="JGI Proposal Number *"
          class="mt-4"
          variant="outlined"
          validate-on-blur
        />
      </div>
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
        :disabled="templateHasData(HARMONIZER_TEMPLATES.jgi_mg?.sampleDataSlot) || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metagenome (Long Read)"
        value="mg-lr-jgi"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.jgi_mg_lr?.sampleDataSlot) || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metatranscriptome"
        value="mt-jgi"
        :disabled="templateHasData(HARMONIZER_TEMPLATES.jgi_mt?.sampleDataSlot) || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metabolome"
        value="mb-jgi"
        disabled
        hide-details
      />
    </div>
  </div>
</template>
