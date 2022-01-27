<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import NmdcSchema from '@/data/nmdc-schema/jsonschema/nmdc.schema.json';
import { studyForm, studyFormValid } from '../store';

export default defineComponent({
  setup() {
    const formRef = ref();

    function addContributor() {
      studyForm.contributors.push({
        name: '',
        orcid: '',
        roles: [],
      });
    }

    function requiredRules(msg: string, otherRules: ((v: string) => unknown)[] = []) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    return {
      formRef,
      studyForm,
      studyFormValid,
      NmdcSchema,
      addContributor,
      requiredRules,
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
      style="max-width: 1000px;"
    >
      <v-text-field
        v-model="studyForm.studyName"
        :rules="requiredRules('Name is required',[
          v => v.length > 6 || 'Study name too short',
        ])"
        validate-on-blur
        label="Project / Study Name *"
        :hint="NmdcSchema.$defs.Study.properties.name.description"
        persistent-hint
        outlined
        dense
        class="my-2"
      />
      <div class="d-flex">
        <v-text-field
          v-model="studyForm.piName"
          label="Principal Investigator Name"
          :hint="NmdcSchema.$defs.Study.properties.principal_investigator.description"
          persistent-hint
          outlined
          dense
          class="my-2 mr-4"
        />
        <v-text-field
          v-model="studyForm.piEmail"
          label="Principal Investigator Email *"
          :rules="requiredRules('E-mail is required',[
            v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
          ])"
          type="email"
          required
          outlined
          dense
          class="my-2"
        />
      </div>
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
      <div class="text-h4">
        Contributors
      </div>
      <div class="text-body-1 mb-2">
        {{ NmdcSchema.$defs.Person.description }}
      </div>
      <div
        v-for="contributor, i in studyForm.contributors"
        :key="`contributor${i}`"
        class="d-flex"
      >
        <v-card class="d-flex flex-column grow pa-4 mb-4">
          <div class="d-flex">
            <v-text-field
              v-model="contributor.name"
              :rules="requiredRules('Full name is required')"
              label="Full name *"
              :hint="NmdcSchema.$defs.Person.properties.name.description"
              outlined
              dense
              persistent-hint
              class="mb-2 mr-3"
            />
            <v-combobox
              v-model="contributor.roles"
              :rules="[(v) => v.length >= 1 || 'At least one role is required']"
              label="Roles *"
              hint="CRediT roles associated with this contributor"
              deletable-chips
              multiple
              outlined
              chips
              small-chips
              dense
              persistent-hint
              :style="{ maxWidth: '400px'}"
            />
          </div>
          <v-text-field
            v-model="contributor.orcid"
            :rules="requiredRules('ORCiD is required')"
            :hint="NmdcSchema.$defs.Person.properties.id.description"
            label="ORCiD *"
            outlined
            persistent-hint
            dense
          />
        </v-card>
        <v-btn
          icon
          @click="studyForm.contributors.splice(i, 1)"
        >
          <v-icon>mdi-minus-circle</v-icon>
        </v-btn>
      </div>
      <v-btn
        depressed
        @click="addContributor"
      >
        <v-icon class="pr-1">
          mdi-plus-circle
        </v-icon>
        Add Contributor
      </v-btn>
    </v-form>
    <strong>* indicates required field</strong>
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
