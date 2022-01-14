<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { multiOmicsForm } from '../store';

export default defineComponent({
  setup() {
    const valid = ref(true);
    const formRef = ref();

    return {
      formRef,
      multiOmicsForm,
      valid,
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
      v-model="valid"
      class="my-6"
      style="max-width: 600px;"
    >
      <v-text-field
        v-model="multiOmicsForm.datasetDoi"
        label="Dataset DOI *"
        required
        outlined
        dense
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
        v-model="multiOmicsForm.studyNumber"
        label="EMSL Proposal / Study Number *"
        outlined
        dense
      />
      <v-text-field
        v-model="multiOmicsForm.GOLDStudyId"
        label="GOLD Study ID"
        required
        outlined
        dense
      />
      <v-text-field
        v-model="multiOmicsForm.JGIStudyId"
        label="JGI Study ID"
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
      <v-radio-group
        v-model="multiOmicsForm.dataWasGenerated"
        label="Data has already been generated?"
      >
        <v-radio
          :value="false"
          label="No"
        />
        <v-radio
          :value="true"
          label="Yes"
        />
      </v-radio-group>
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
