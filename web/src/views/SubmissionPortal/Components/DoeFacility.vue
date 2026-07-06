<script lang="ts">
import { computed, defineComponent } from 'vue';
import { HARMONIZER_TEMPLATES, JGI_TEMPLATE_NAMES } from '@/views/SubmissionPortal/types';
import Definitions from '@/definitions';
import SubmissionContextShippingForm from './SubmissionContextShippingForm.vue';
import { useSubmissionStore } from '../store';

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
  emits: ['revalidate', 'add-award-doi'],

  setup(_, { emit }) {
    const store = useSubmissionStore();
    const { templateHasData } = store;
    const multiOmicsForm = computed(() => store.sampleSet.forms.multiOmicsForm);
    const selectedFacilities = () => multiOmicsForm.value.facilities ?? [];

    function facilityChange() {
      if (multiOmicsForm.value.awardDois === null || multiOmicsForm.value.awardDois.length < selectedFacilities().length) {
        emit('add-award-doi');
      }
      emit('revalidate');
    }

    return {
      facilityChange,
      selectedFacilities,
      Definitions,
      multiOmicsForm,
      templateHasData,
      HARMONIZER_TEMPLATES,
      JGI_TEMPLATE_NAMES,
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
      :disabled="templateHasData('emsl') || undefined"
      @change="facilityChange"
    />
    <div
      v-if="selectedFacilities().includes('EMSL')"
      class="mb-4 ml-4"
    >
      <v-text-field
        v-if="selectedFacilities().includes('EMSL')"
        v-model="multiOmicsForm.studyNumber"
        :rules="[
          v => !!v || 'EMSL Proposal Number is required when processing was done at EMSL',
          v => /^\d{5}$/.test(v) || 'EMSL Proposal Number must be a 5 digit numerical value'
        ]"
        hint="EMSL Proposal Number is required when processing was done at EMSL"
        persistent-hint
        label="EMSL Proposal Number *"
        class="mb-4"
        variant="outlined"
        validate-on-blur
      />
      <v-radio-group
        v-if="multiOmicsForm.dataGenerated === false && selectedFacilities().includes('EMSL')"
        v-model="multiOmicsForm.ship"
        label="Will samples be shipped? *"
        class="mb-4"
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
        v-if="multiOmicsForm.dataGenerated === false && multiOmicsForm.ship && selectedFacilities().includes('EMSL')"
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
        :disabled="templateHasData('emsl') || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metaproteome"
        value="mp-emsl"
        :disabled="templateHasData('emsl') || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metabolome"
        value="mb-emsl"
        :disabled="templateHasData('emsl') || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Natural Organic Matter (FT-ICR MS)"
        value="nom-emsl"
        :disabled="templateHasData('emsl') || undefined"
        hide-details
      />
    </div>
    <v-checkbox
      v-model="multiOmicsForm.facilities"
      label="JGI"
      value="JGI"
      hide-details
      :disabled="templateHasData(JGI_TEMPLATE_NAMES) || undefined"
      @change="facilityChange"
    />
    <div
      v-if="selectedFacilities().includes('JGI')"
      class="mb-4 ml-4"
    >
      <div class="d-flex flex-column grow">
        <v-text-field
          v-if="selectedFacilities().includes('JGI')"
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
        :disabled="templateHasData('jgi_mg') || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metagenome (Long Read)"
        value="mg-lr-jgi"
        :disabled="templateHasData('jgi_mg_lr') || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Metatranscriptome"
        value="mt-jgi"
        :disabled="templateHasData('jgi_mt') || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Isolate Genome"
        value="isolate-genome-jgi"
        :disabled="templateHasData('jgi_isolate_genome') || undefined"
        hide-details
      />
      <v-checkbox
        v-model="multiOmicsForm.omicsProcessingTypes"
        label="Isolate Transcriptome"
        value="isolate-transcriptome-jgi"
        :disabled="templateHasData('jgi_isolate_transcriptome') || undefined"
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
