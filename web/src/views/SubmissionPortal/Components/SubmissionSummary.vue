<script lang="ts">
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
import {
  computed,
  defineComponent,
  ref,
} from '@vue/composition-api';
import Definitions from '@/definitions';
import doiProviderValues from '@/schema';
import {
  validForms,
  canEditSubmissionMetadata,
  isOwner,
} from '../store';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';

export default defineComponent({
  components: { SubmissionPermissionBanner },
  setup() {
    const textVal = ref('');

    function createNewStudyID() {
      textVal.value = 'New unique ID created';
    }

    const canSubmit = computed(() => (validForms.templatesValid && validForms.harmonizerValid && validForms.studyFormValid && validForms.multiOmicsFormValid && isOwner() && false));

    return {
      validForms,
      NmdcSchema,
      Definitions,
      doiProviderValues,
      textVal,
      canSubmit,
      canEditSubmissionMetadata,
      createNewStudyID,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Submission Summary
    </div>
    <div class="text-h5">
      Status and links to each portion of your submission. You may also link this submission to an existing study, or create a new study ID here.
    </div>
    <submission-permission-banner
      v-if="!canEditSubmissionMetadata()"
    />
    <div class="my-4">
      <div class="text-h5">
        Study Form Status
        <v-icon> {{ validForms.studyFormValid ? 'mdi-check' : 'mdi-close-circle' }} </v-icon>
      </div>
      <v-btn
        color="primary"
        depressed
        :to="{ name: 'Study Form' }"
      >
        Go to Study Form
        <v-icon class="pl-1">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
    <div class="my-4">
      <div class="text-h5">
        Multi-Omics Form Status
        <v-icon> {{ validForms.multiOmicsFormValid ? 'mdi-check' : 'mdi-close-circle' }} </v-icon>
      </div>
      <v-btn
        color="primary"
        depressed
        :to="{ name: 'Multiomics Form' }"
      >
        Go to Multiomics Form
        <v-icon class="pl-1">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
    <div class="my-4">
      <div class="text-h5">
        Sample Environment/Template status
        <v-icon> {{ validForms.templatesValid ? 'mdi-check' : 'mdi-close-circle' }} </v-icon>
      </div>
      <v-btn
        color="primary"
        depressed
        :to="{ name: 'Sample Environment' }"
      >
        Go to Sample Environment
        <v-icon class="pl-1">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
    <div class="my-4">
      <div class="text-h5">
        Data Harmonizer Status
        <v-icon> {{ validForms.harmonizerValid ? 'mdi-check' : 'mdi-close-circle' }} </v-icon>
      </div>
      <v-btn
        color="primary"
        depressed
        :to="{ name: 'Submission Sample Editor' }"
      >
        Go to Data Harmonizer
        <v-icon class="pl-1">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
    <div class="text-h5">
      Create or Add Existing Study ID
    </div>
    <div class="d-flex">
      <v-text-field
        v-model="textVal"
        label="NMDC study ID"
        persistent-hint
        outlined
        dense
        class="mb-2 mr-3"
      />
      <v-btn
        color="gray"
        :disabled="textVal.length!=0"
        depressed
        @click="createNewStudyID()"
      >
        <v-icon class="pl-1">
          mdi-plus
        </v-icon>
        Create New ID
      </v-btn>
    </div>
    <div class="d-flex">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Submission Home' }"
      >
        <v-icon class="pl-1">
          mdi-arrow-left-circle
        </v-icon>
        Go to Submission List
      </v-btn>
      <v-spacer />
      <v-btn
        color="success"
        depressed
        :disabled="!canSubmit"
        @click="true"
      >
        Submit
      </v-btn>
    </div>
  </div>
</template>
