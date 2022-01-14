<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { studyForm } from '../store';

export default defineComponent({
  setup() {
    const valid = ref(true);
    const formRef = ref();

    return {
      formRef,
      studyForm,
      valid,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Study Information
    </div>
    <div class="text-h5">
      Information about the study associated with your samples.
    </div>
    <v-form
      ref="formRef"
      v-model="valid"
      class="my-6"
      style="max-width: 600px;"
    >
      <v-text-field
        v-model="studyForm.studyName"
        label="Project / Study Name *"
        hint="This is a description"
        persistent-hint
        required
        outlined
        dense
      />
      <v-text-field
        v-model="studyForm.piName"
        label="Principal Investigator Name"
        outlined
        dense
      />
      <v-text-field
        v-model="studyForm.piEmail"
        label="Principal Investigator Email *"
        required
        outlined
        dense
      />
      <v-text-field
        v-model="studyForm.piOrcid"
        label="Principal Investigator ORCiD"
        outlined
        dense
      />
      <v-text-field
        v-model="studyForm.linkOutWebpage"
        label="LinkOut webpage"
        outlined
        dense
      />
      <v-textarea
        v-model="studyForm.description"
        label="Study Description"
        outlined
        dense
      />
      <v-text-field
        v-model="studyForm.notes"
        label="Optional Notes"
        outlined
        dense
      />
    </v-form>
    <div class="d-flex">
      <v-spacer />
      <v-btn
        color="primary"
        depressed
        :to="{ name: 'Multiomics Form' }"
      >
        Go to next step
        <v-icon class="pl-1">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
  </div>
</template>
