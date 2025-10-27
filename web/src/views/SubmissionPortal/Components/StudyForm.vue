<script lang="ts">
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
import {
  computed,
  defineComponent,
  onMounted,
  ref,
  Ref,
} from 'vue';
import Definitions from '@/definitions';
import doiProviderValues from '@/schema';
import { PermissionTitle } from '@/views/SubmissionPortal/types';
import { stateRefs } from '@/store';
import {
  multiOmicsForm,
  studyForm,
  studyFormValid,
  permissionTitleToDbValueMap,
  isOwner,
  canEditSubmissionMetadata,
  checkDoiFormat,
} from '../store';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';

export default defineComponent({
  components: { SubmissionDocsLink, SubmissionPermissionBanner },
  setup() {
    const formRef = ref();

    const currentUserOrcid = computed(() => stateRefs.user.value?.orcid);

    const permissionHelpText = ref([
      {
        title: 'Viewer',
        description: 'Viewers can see all components of a submission, but cannot edit.',
      },
      {
        title: 'Metadata Contributor',
        description: 'Metadata contributors can view all components of a submission and can only edit the sample metadata information on the last step of the submission process.',
      },
      {
        title: 'Editor',
        description: 'Editors of a submission have full permission to edit every aspect of the submission with the exception of permission levels.',
      },
      {
        title: 'Owner',
        description: 'This level of permission is automatically assigned to the submission author and Principal Investigator. These users can edit every aspect of the submission.',
      },
    ]);

    function addContributor() {
      studyForm.contributors.push({
        name: '',
        orcid: '',
        roles: [],
        permissionLevel: null,
      });
    }

    function addFundingSource() {
      if (studyForm.fundingSources === null || studyForm.fundingSources.length === 0) {
        studyForm.fundingSources = [''];
      } else {
        studyForm.fundingSources.push('');
      }
    }

    function addDataDoi() {
      if (!Array.isArray(studyForm.dataDois)) {
        studyForm.dataDois = [];
      }
      studyForm.dataDois.push({
        value: '',
        provider: '',
      });
    }

    function requiredRules(msg: string, otherRules: ((v: string) => unknown)[] = []) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    const orcidRequiredRule = (idx: number) => (v: string) => {
      if (idx > studyForm.contributors.length) return true;
      const contributor = studyForm.contributors[idx];
      // show error when: permission level exists, but orcid does not
      return (contributor.permissionLevel && !!v) || !contributor.permissionLevel || 'ORCID iD is required if a permission level is specified';
    };

    const uniqueOrcidRule = (idx: number) => (v: string) => {
      if (idx > studyForm.contributors.length || !v) return true;
      const existingOrcids = new Set(studyForm.contributors.filter((contributor, contributorListIndex) => idx !== contributorListIndex).map((contributor) => contributor.orcid));
      return !existingOrcids.has(v) || 'ORCID iDs must be unique';
    };

    const permissionLevelChoices: Ref<{ title: string, value: string }[]> = ref([]);
    Object.keys(permissionTitleToDbValueMap).forEach((title) => {
      permissionLevelChoices.value.push({
        title,
        value: permissionTitleToDbValueMap[title as PermissionTitle],
      });
    });

    onMounted(async () => {
      formRef.value.validate();
    });

    return {
      formRef,
      studyForm,
      multiOmicsForm,
      studyFormValid,
      NmdcSchema,
      Definitions,
      addContributor,
      addFundingSource,
      addDataDoi,
      doiProviderValues,
      requiredRules,
      permissionLevelChoices,
      isOwner,
      canEditSubmissionMetadata,
      orcidRequiredRule,
      uniqueOrcidRule,
      currentUserOrcid,
      permissionHelpText,
      checkDoiFormat,
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Study Information
      <submission-docs-link anchor="study" />
    </div>
    <div class="text-h5">
      {{ NmdcSchema.classes.Study.description }}
    </div>
    <submission-permission-banner
      v-if="!canEditSubmissionMetadata()"
    />
    <v-form
      ref="formRef"
      v-model="studyFormValid"
      class="my-6"
      style="max-width: 1000px;"
      :disabled="!canEditSubmissionMetadata()"
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
        variant="outlined"
        dense
        class="my-2"
      />
      <div class="d-flex">
        <v-text-field
          v-model="studyForm.piName"
          label="Principal Investigator Name"
          :hint="Definitions.piName"
          persistent-hint
          variant="outlined"
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
          variant="outlined"
          dense
          class="my-2"
        />
      </div>
      <v-text-field
        v-model="studyForm.piOrcid"
        label="Principal Investigator ORCID"
        :disabled="!isOwner() || currentUserOrcid === studyForm.piOrcid"
        variant="outlined"
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
        variant="outlined"
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
        variant="outlined"
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
        variant="outlined"
        dense
        class="my-2"
      />
      <div class="text-h4">
        Funding Sources
      </div>
      <div class="text-body-1 mb-2">
        {{ "Sources of funding for this study." }}
      </div>
      <div
        v-for="_, i in studyForm.fundingSources"
        :key="`fundingSource${i}`"
        class="d-flex"
      >
        <v-card class="d-flex flex-column grow pa-4 mb-4">
          <div class="d-flex">
            <v-text-field
              v-if="studyForm.fundingSources !== null"
              v-model="studyForm.fundingSources[i]"
              label="Funding Source *"
              :hint="Definitions.fundingSources"
              persistent-hint
              variant="outlined"
              dense
              class="mb-2 mr-3"
              :error-messages="studyForm.fundingSources[i] ? undefined : ['Field cannot be empty.']"
            >
              <template #message="{ message }">
                <span v-html="message" />
              </template>
            </v-text-field>
          </div>
        </v-card>
        <v-btn
          v-if="studyForm.fundingSources !== null"
          icon
          :disabled="!isOwner()"
          @click="studyForm.fundingSources.splice(i, 1)"
        >
          <v-icon>mdi-minus-circle</v-icon>
        </v-btn>
      </div>
      <v-btn
        class="mb-4"
        depressed
        :disabled="!canEditSubmissionMetadata()"
        @click="addFundingSource"
      >
        <v-icon class="pr-1">
          mdi-plus-circle
        </v-icon>
        Add Funding Source
      </v-btn>
      <template #message="{ message }">
        <span v-html="message" />
      </template>
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
              label="Full name *"
              :hint="Definitions.contributorFullName"
              variant="outlined"
              dense
              persistent-hint
              :error-messages="contributor.name ? undefined : ['Field cannot be empty.']"
              class="mb-2 mr-3"
            />
            <v-text-field
              v-model="contributor.orcid"
              :rules="[orcidRequiredRule(i), uniqueOrcidRule(i)]"
              :hint="Definitions.contributorOrcid"
              :disabled="currentUserOrcid === contributor.orcid"
              label="ORCID"
              variant="outlined"
              persistent-hint
              dense
              :style="{ maxWidth: '400px'}"
            >
              <template #message="{ message }">
                <span v-html="message" />
              </template>
            </v-text-field>
          </div>
          <div class="d-flex">
            <v-select
              v-model="contributor.roles"
              :items="Object.keys(NmdcSchema.enums.CreditEnum.permissible_values)"
              label="CRediT Roles *"
              :hint="Definitions.contributorRoles"
              deletable-chips
              multiple
              variant="outlined"
              chips
              small-chips
              dense
              persistent-hint
              :error-messages="!contributor.roles || contributor.roles.length === 0 ? ['At least one role is required'] : undefined"
              class="mb-2 mr-3"
            >
              <template #message="{ message }">
                <span v-html="message" />
              </template>
            </v-select>
            <v-select
              v-if="isOwner()"
              v-model="contributor.permissionLevel"
              :items="permissionLevelChoices"
              clearable
              item-text="title"
              item-value="value"
              :style="{ maxWidth: '400px'}"
              label="Permission Level"
              hint="Level of permissions the contributor has for this submission"
              variant="outlined"
              dense
              persistent-hint
              @change="() => formRef.validate()"
            >
              <template #prepend-inner>
                <v-tooltip
                  bottom
                  max-width="500px"
                >
                  <template #activator="{on, attrs}">
                    <v-btn
                      icon
                      small
                      v-bind="attrs"
                      v-on="on"
                    >
                      <v-icon>mdi-help-circle</v-icon>
                    </v-btn>
                  </template>
                  <div
                    v-for="role in permissionHelpText"
                    :key="role.title"
                    class="pb-2"
                  >
                    <strong>{{ role.title }}: </strong><span>{{ role.description }}</span>
                  </div>
                </v-tooltip>
              </template>
            </v-select>
          </div>
        </v-card>
        <v-btn
          icon
          :disabled="!isOwner() || currentUserOrcid === contributor.orcid"
          @click="studyForm.contributors.splice(i, 1)"
        >
          <v-icon>mdi-minus-circle</v-icon>
        </v-btn>
      </div>
      <v-btn
        depressed
        :disabled="!canEditSubmissionMetadata()"
        class="mb-4"
        @click="addContributor"
      >
        <v-icon class="pr-1">
          mdi-plus-circle
        </v-icon>
        Add Contributor
      </v-btn>

      <div class="text-h4">
        Data DOIs
      </div>
      <div class="text-body-1 mb-2">
        {{ "Data DOIs for this study" }}
      </div>
      <div
        v-for="_, i in studyForm.dataDois"
        :key="`dataDois${i}`"
        class="d-flex"
      >
        <v-card class="d-flex flex-column grow pa-4 mb-4">
          <div class="d-flex">
            <v-text-field
              v-if="studyForm.dataDois !== null"
              v-model="studyForm.dataDois[i].value"
              label="Data DOI value *"
              :hint="Definitions.dataDoiValue"
              persistent-hint
              variant="outlined"
              dense
              required
              class="mb-2 mr-3"
              :rules="requiredRules('DOI value must be provided',[
                v => checkDoiFormat(v) || 'DOI must be valid',
              ])"
            >
              <template #message="{ message }">
                <span v-html="message" />
              </template>
            </v-text-field>
            <v-select
              v-if="studyForm.dataDois !== null"
              v-model="studyForm.dataDois[i].provider"
              label="Data DOI Provider *"
              :hint="Definitions.dataDoiProvider"
              :items="doiProviderValues"
              persistent-hint
              variant="outlined"
              dense
              clearable
              class="mb-2 mr-3"
              :rules="studyForm.dataDois[i].provider ? undefined : ['A provider must be selected.']"
            >
              <template #message="{ message }">
                <span v-html="message" />
              </template>
            </v-select>
          </div>
        </v-card>
        <v-btn
          v-if="studyForm.dataDois !== null"
          icon
          :disabled="!isOwner()"
          @click="studyForm.dataDois.splice(i, 1)"
        >
          <v-icon>mdi-minus-circle</v-icon>
        </v-btn>
      </div>
      <v-btn
        class="mb-4"
        depressed
        :disabled="!canEditSubmissionMetadata()"
        @click="addDataDoi"
      >
        <v-icon class="pr-1">
          mdi-plus-circle
        </v-icon>
        Add Data DOI
      </v-btn>

      <div class="text-h4">
        External Identifiers
        <v-text-field
          v-model="studyForm.GOLDStudyId"
          label="GOLD Study ID"
          :hint="Definitions.studyGoldID"
          persistent-hint
          variant="outlined"
          dense
        />
        <v-text-field
          v-model="studyForm.NCBIBioProjectId"
          label="NCBI BioProject Accession"
          :hint="Definitions.studyNCBIBioProjectAccession"
          persistent-hint
          variant="outlined"
          dense
        />
        <v-combobox
          v-model="studyForm.alternativeNames"
          label="Alternative Names / IDs"
          :hint="Definitions.studyAlternativeNames"
          persistent-hint
          deletable-chips
          multiple
          variant="outlined"
          chips
          small-chips
          dense
          append-icon=""
        />
      </div>
    </v-form>
    <strong>* indicates required field</strong>
    <div class="d-flex mt-5">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Submission Home' }"
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
