<script lang="ts">
import { defineComponent, onMounted, ref } from '@vue/composition-api';
import NmdcSchema from 'nmdc-schema/jsonschema/nmdc.schema.json';
import { cloneDeep } from 'lodash';
import Definitions from '@/definitions';
import { studyForm, studyFormValid } from '../store';
import SubmissionTable from './SubmissionTable.vue';
import { MetadataSubmissionRecord } from '../store/api';

export default defineComponent({
  components: {
    SubmissionTable,
  },
  setup() {
    const formRef = ref();
    const copyDataDialog = ref(false);

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

    function copyInfoClicked() {
      copyDataDialog.value = true;
    }

    function copyData(item: MetadataSubmissionRecord) {
      const newStudyData = cloneDeep(item.metadata_submission.studyForm);
      Object.assign(studyForm, newStudyData);
      formRef.value.validate();
      copyDataDialog.value = false;
    }

    onMounted(() => {
      formRef.value.validate();
    });

    return {
      formRef,
      copyDataDialog,
      studyForm,
      studyFormValid,
      NmdcSchema,
      Definitions,
      addContributor,
      requiredRules,
      copyData,
      copyInfoClicked,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Study Information
    </div>
    <div class="text-h5 mb-1">
      {{ NmdcSchema.$defs.Study.description }}
    </div>
    <v-btn
      color="primary"
      depressed
      @click="copyInfoClicked"
    >
      <v-icon class="pr-1">
        mdi-content-copy
      </v-icon>
      Copy from another submission
      <v-dialog
        v-model="copyDataDialog"
        activator="parent"
        width="auto"
      >
        <v-card>
          <v-card-title>
            Copy Study Data
          </v-card-title>
          <v-card-text>Copy study data from an existing submission.</v-card-text>
          <submission-table
            :action-title="`Copy`"
            @submissionSelected="copyData"
          />
          <v-card-actions>
            <v-btn
              @click="copyDataDialog = false"
            >
              Cancel
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-btn>
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
        label="Study Name *"
        :hint="Definitions.studyName"
        persistent-hint
        outlined
        dense
        class="my-2"
      />
      <div class="d-flex">
        <v-text-field
          v-model="studyForm.piName"
          label="Principal Investigator Name"
          :hint="Definitions.piName"
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
          :hint="Definitions.piEmail"
          persistent-hint
          type="email"
          required
          outlined
          dense
          class="my-2"
        />
      </div>
      <v-text-field
        v-model="studyForm.piOrcid"
        label="Principal Investigator ORCID"
        outlined
        :hint="Definitions.piOrcid"
        persistent-hint
        dense
        class="my-2"
      >
        <template #message="{ message }">
          <span v-html="message" />
        </template>
      </v-text-field>
      <v-combobox
        v-model="studyForm.linkOutWebpage"
        label="Webpage Links"
        :hint="Definitions.linkOutWebpage"
        persistent-hint
        outlined
        dense
        multiple
        small-chips
        clearable
        class="my-2"
      />
      <v-textarea
        v-model="studyForm.description"
        label="Study Description"
        :hint="Definitions.studyDescription"
        persistent-hint
        outlined
        dense
        class="my-2"
      >
        <template #message="{ message }">
          <span v-html="message" />
        </template>
      </v-textarea>
      <v-text-field
        v-model="studyForm.notes"
        label="Optional Notes"
        :hint="Definitions.studyOptionalNotes"
        persistent-hint
        outlined
        dense
        class="my-2"
      />
      <div class="text-h4">
        Contributors
      </div>
      <div class="text-body-1 mb-2">
        {{ Definitions.studyContributors }}
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
              :hint="Definitions.contributorFullName"
              outlined
              dense
              persistent-hint
              class="mb-2 mr-3"
            />
            <v-text-field
              v-model="contributor.orcid"
              :hint="Definitions.contributorOrcid"
              label="ORCID"
              outlined
              persistent-hint
              dense
              :style="{ maxWidth: '400px'}"
            >
              <template #message="{ message }">
                <span v-html="message" />
              </template>
            </v-text-field>
          </div>
          <v-select
            v-model="contributor.roles"
            :rules="[v => v.length >= 1 || 'At least one role is required']"
            :items="NmdcSchema.$defs.CreditEnum.enum"
            label="Roles *"
            :hint="Definitions.contributorRoles"
            deletable-chips
            multiple
            outlined
            chips
            small-chips
            dense
            persistent-hint
          >
            <template #message="{ message }">
              <span v-html="message" />
            </template>
          </v-select>
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
    <div class="d-flex mt-5">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Submission Context' }"
      >
        <v-icon class="pl-1">
          mdi-arrow-left-circle
        </v-icon>
        Go to previous step
      </v-btn>
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
