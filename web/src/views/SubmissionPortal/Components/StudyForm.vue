<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import NmdcSchema from '@/data/nmdc-schema/jsonschema/nmdc.schema.json';
import { studyForm, studyFormValid } from '../store';

export default defineComponent({
  setup() {
    const formRef = ref();

    return {
      formRef,
      studyForm,
      studyFormValid,
      NmdcSchema,
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
      {{ NmdcSchema.$defs.Study.description }}
    </div>
    <v-form
      ref="formRef"
      v-model="studyFormValid"
      class="my-6"
      style="max-width: 600px;"
    >
      <v-text-field
        v-model="studyForm.studyName"
        :rules="[
          v => !!v || 'Name is required',
          v => v.length > 6 || 'Study name too short',
        ]"
        validate-on-blur
        label="Project / Study Name *"
        :hint="NmdcSchema.$defs.Study.properties.name.description"
        persistent-hint
        outlined
        dense
        class="my-2"
      />
      <v-text-field
        v-model="studyForm.piName"
        label="Principal Investigator Name"
        :hint="NmdcSchema.$defs.Study.properties.principal_investigator.description"
        persistent-hint
        outlined
        dense
        class="my-2"
      />
      <v-text-field
        v-model="studyForm.piEmail"
        label="Principal Investigator Email *"
        :rules="[
          v => !!v || 'E-mail is required',
          v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
        ]"
        type="email"
        required
        outlined
        dense
        class="my-2"
      />
      <v-text-field
        v-model="studyForm.piOrcid"
        label="Principal Investigator ORCiD"
        outlined
        dense
        class="my-2"
      />
      <v-text-field
        v-model="studyForm.linkOutWebpage"
        label="LinkOut webpage"
        outlined
        dense
        class="my-2"
      />
      <v-textarea
        v-model="studyForm.description"
        label="Study Description"
        :hint="NmdcSchema.$defs.Study.properties.description.description"
        persistent-hint
        outlined
        dense
        class="my-2"
      />
      <v-text-field
        v-model="studyForm.notes"
        label="Optional Notes"
        outlined
        dense
        class="my-2"
      />
    </v-form>
    <div class="d-flex">
      <v-spacer />
      <v-btn
        color="primary"
        depressed
        :disabled="!studyFormValid"
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
