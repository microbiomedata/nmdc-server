<script lang="ts">
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';
import {
  computed,
  defineComponent,
  onMounted,
  ref,
  Ref,
} from 'vue';
import Definitions from '@/definitions';
import doiProviderValues from '@/schema';
import {
  multiOmicsForm,
  studyForm,
  studyFormValid,
  permissionTitleToDbValueMap,
  isOwner,
  canEditSubmissionMetadata,
  checkDoiFormat,
  primaryStudyImageUrl,
  piImageUrl,
  canEditSubmissionByStatus,
  SubmissionStatusTitleMapping,
  status,
} from '../store';
import { PermissionTitle } from '@/views/SubmissionPortal/types';
import { stateRefs } from '@/store';
import SubmissionDocsLink from './SubmissionDocsLink.vue';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';
import ImageUpload from './ImageUpload.vue';
import StatusAlert from './StatusAlert.vue';
import { ValidationResult } from 'vuetify/lib/composables/validation.mjs';

export default defineComponent({
  components: {
    ImageUpload,
    SubmissionDocsLink,
    SubmissionPermissionBanner,
    StatusAlert,
  },
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

    function requiredRules(msg: string, otherRules: ((_v: string) => ValidationResult)[] = []) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    const orcidRequiredRule = (idx: number) => (v: string) => {
      if (idx > studyForm.contributors.length) return true;
      const contributor = studyForm.contributors[idx];
      // show error when: permission level exists, but orcid does not
      return (contributor?.permissionLevel && !!v) || !contributor?.permissionLevel || 'ORCID iD is required if a permission level is specified';
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
      primaryStudyImageUrl,
      piImageUrl,
      canEditSubmissionByStatus,
      SubmissionStatusTitleMapping,
      status,
      StatusAlert,
    };
  },
});
</script>

<template>
  <div>
    <h1 class="text-h2">
      Study Information
      <submission-docs-link anchor="study" />
    </h1>
    <div class="text-h5">
      {{ NmdcSchema.classes.Study.description }}
    </div>
    <submission-permission-banner
      v-if="canEditSubmissionByStatus() && !canEditSubmissionMetadata()"
    />
    <StatusAlert v-if="!canEditSubmissionByStatus()" />
    <v-form
      ref="formRef"
      v-model="studyFormValid"
      class="my-6"
      style="max-width: 1000px;"
      :disabled="!canEditSubmissionMetadata()"
    >
      <div class="stack-md">
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
        />
        <v-textarea
          v-model="studyForm.description"
          label="Study Description"
          :hint="Definitions.studyDescription"
          persistent-hint
          variant="outlined"
        >
          <template #message="{ message }">
            <span v-html="message" />
          </template>
        </v-textarea>
        <v-combobox
          v-model="studyForm.linkOutWebpage"
          label="Webpage Links"
          :hint="Definitions.linkOutWebpage"
          persistent-hint
          variant="outlined"
          multiple
          small-chips
          clearable
        />
        <v-text-field
          v-model="studyForm.notes"
          label="Optional Notes"
          :hint="Definitions.studyOptionalNotes"
          persistent-hint
          variant="outlined"
        />
        <ImageUpload
          input-label="Study Image"
          :input-hint="Definitions.studyImage"
          input-icon="mdi-image"
          :image-url="primaryStudyImageUrl"
          image-type="primary_study_image"
          @on-upload-success="(updated) => {
            primaryStudyImageUrl = updated.primary_study_image_url;
          }"
          @on-delete-success="() => {
            primaryStudyImageUrl = null
          }"
        />
      </div>

      <div class="text-h4 mt-8">
        Principal Investigator
      </div>
      <div class="stack-md">
        <v-text-field
          v-model="studyForm.piName"
          label="Name"
          :hint="Definitions.piName"
          persistent-hint
          variant="outlined"
        />
        <v-text-field
          v-model="studyForm.piEmail"
          label="Email *"
          :rules="requiredRules('E-mail is required',[
            v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
          ])"
          :hint="Definitions.piEmail"
          persistent-hint
          type="email"
          required
          variant="outlined"
        />
        <v-text-field
          v-model="studyForm.piOrcid"
          label="ORCID iD"
          :disabled="!isOwner() || currentUserOrcid === studyForm.piOrcid || undefined"
          variant="outlined"
          :hint="Definitions.piOrcid"
          persistent-hint
        >
          <template #message="{ message }">
            <span v-html="message" />
          </template>
        </v-text-field>
        <ImageUpload
          is-avatar
          input-label="Image"
          :input-hint="Definitions.piHeadshotImage"
          input-icon="mdi-account-box"
          :image-url="piImageUrl"
          image-type="pi_image"
          @on-upload-success="(updated) => {
            piImageUrl = updated.pi_image_url;
          }"
          @on-delete-success="() => {
            piImageUrl = null
          }"
        />
      </div>

      <div class="text-h4 mt-8">
        Funding Sources
      </div>
      <div class="text-body-1 mb-2">
        Sources of funding for this study.
      </div>
      <div
        v-for="_, i in studyForm.fundingSources"
        :key="`fundingSource${i}`"
        class="d-flex"
      >
        <v-card class="d-flex flex-column flex-fill pa-4 mb-4">
          <div class="d-flex">
            <v-text-field
              v-if="studyForm.fundingSources !== null"
              v-model="studyForm.fundingSources[i]"
              label="Funding Source *"
              :hint="Definitions.fundingSources"
              persistent-hint
              variant="outlined"
              class="mr-3"
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
          variant="plain"
          :disabled="!isOwner()"
          @click="studyForm.fundingSources.splice(i, 1)"
        >
          <v-icon>mdi-minus-circle</v-icon>
        </v-btn>
      </div>
      <v-btn-grey
        class="mb-4"
        :disabled="!canEditSubmissionMetadata()"
        @click="addFundingSource"
      >
        <v-icon class="pr-1">
          mdi-plus-circle
        </v-icon>
        Add Funding Source
      </v-btn-grey>

      <div class="text-h4 mt-8">
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
        <v-card class="d-flex flex-column flex-fill pa-4 mb-4">
          <div class="d-flex">
            <v-text-field
              v-model="contributor.name"
              label="Full name *"
              :hint="Definitions.contributorFullName"
              variant="outlined"
              persistent-hint
              :error-messages="contributor.name ? undefined : ['Field cannot be empty.']"
              class="mr-3"
            />
            <v-text-field
              v-model="contributor.orcid"
              :rules="[orcidRequiredRule(i), uniqueOrcidRule(i)]"
              :hint="Definitions.contributorOrcid"
              :disabled="currentUserOrcid === contributor.orcid || undefined"
              label="ORCID"
              variant="outlined"
              persistent-hint
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
              persistent-hint
              :error-messages="!contributor.roles || contributor.roles.length === 0 ? ['At least one role is required'] : undefined"
              class="mr-3"
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
              persistent-hint
              @change="() => formRef.validate()"
            >
              <template #prepend-inner>
                <v-tooltip
                  bottom
                  max-width="500px"
                >
                  <template #activator="{props}">
                    <v-btn
                      icon
                      size="small"
                      variant="plain"
                      v-bind="props"
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
          variant="plain"
          :disabled="!isOwner() || currentUserOrcid === contributor.orcid || undefined"
          @click="studyForm.contributors.splice(i, 1)"
        >
          <v-icon>mdi-minus-circle</v-icon>
        </v-btn>
      </div>
      <v-btn-grey
        :disabled="!canEditSubmissionMetadata()"
        class="mb-4"
        @click="addContributor"
      >
        <v-icon class="pr-1">
          mdi-plus-circle
        </v-icon>
        Add Contributor
      </v-btn-grey>

      <div class="text-h4 mt-8">
        Data DOIs
      </div>
      <div class="text-body-1 mb-2">
        Data DOIs for this study
      </div>
      <div
        v-for="_, i in studyForm.dataDois"
        :key="`dataDois${i}`"
        class="d-flex"
      >
        <v-card class="d-flex flex-column flex-fill pa-4 mb-4">
          <div class="d-flex">
            <v-text-field
              v-if="studyForm.dataDois !== null"
              v-model="studyForm.dataDois[i]!.value"
              label="Data DOI value *"
              :hint="Definitions.dataDoiValue"
              persistent-hint
              variant="outlined"
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
              v-model="studyForm.dataDois[i]!.provider"
              label="Data DOI Provider *"
              :hint="Definitions.dataDoiProvider"
              :items="doiProviderValues"
              item-title="text"
              item-value="value"
              persistent-hint
              variant="outlined"
              clearable
              class="mb-2 mr-3"
              :rules="studyForm.dataDois[i]?.provider ? undefined : ['A provider must be selected.']"
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
          variant="plain"
          :disabled="!isOwner()"
          @click="studyForm.dataDois.splice(i, 1)"
        >
          <v-icon>mdi-minus-circle</v-icon>
        </v-btn>
      </div>
      <v-btn-grey
        class="mb-4"
        :disabled="!canEditSubmissionMetadata()"
        @click="addDataDoi"
      >
        <v-icon class="pr-1">
          mdi-plus-circle
        </v-icon>
        Add Data DOI
      </v-btn-grey>

      <div class="text-h4 mt-8">
        External Identifiers
      </div>
      <div class="stack-md">
        <v-text-field
          v-model="studyForm.GOLDStudyId"
          label="GOLD Study ID"
          :hint="Definitions.studyGoldID"
          persistent-hint
          variant="outlined"
        />
        <v-text-field
          v-model="studyForm.NCBIBioProjectId"
          label="NCBI BioProject Accession"
          :hint="Definitions.studyNCBIBioProjectAccession"
          persistent-hint
          variant="outlined"
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
          append-icon=""
        />
      </div>
    </v-form>

    <strong>* indicates required field</strong>

    <div class="d-flex mt-5">
      <v-btn-grey :to="{ name: 'Submission Home' }">
        <v-icon class="pr-2">
          mdi-arrow-left-circle
        </v-icon>
        Go to previous step
      </v-btn-grey>
      <v-spacer />
      <v-btn
        color="primary"
        :disabled="!studyFormValid"
        :to="{ name: 'Multiomics Form' }"
      >
        Go to next step
        <v-icon class="pl-2">
          mdi-arrow-right-circle
        </v-icon>
      </v-btn>
    </div>
  </div>
</template>
