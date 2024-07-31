<script lang="ts">
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc.schema.json';
import {
  computed,
  defineComponent,
  onMounted,
  ref,
  Ref,
} from '@vue/composition-api';
import Definitions from '@/definitions';
import {
  studyForm,
  studyFormValid,
  permissionTitleToDbValueMap,
  permissionTitle,
  isOwner,
  canEditSubmissionMetadata,
} from '../store';
import { stateRefs } from '@/store';
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
        value: permissionTitleToDbValueMap[title as permissionTitle],
      });
    });

    onMounted(async () => {
      formRef.value.validate();
    });

    return {
      formRef,
      studyForm,
      studyFormValid,
      NmdcSchema,
      Definitions,
      addContributor,
      requiredRules,
      permissionLevelChoices,
      isOwner,
      canEditSubmissionMetadata,
      orcidRequiredRule,
      uniqueOrcidRule,
      currentUserOrcid,
      permissionHelpText,
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
      {{ NmdcSchema.$defs.Study.description }}
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
        :disabled="!isOwner() || currentUserOrcid === studyForm.piOrcid"
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
        v-model="studyForm.funding_sources"
        label="Funding Source"
        outlined
        :hint="Definitions.funding_sources"
        persistent-hint
        dense
        class="my-2"
      >
        <template #message="{ message }">
          <span v-html="message" />
        </template>
      </v-text-field>
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
              :rules="[orcidRequiredRule(i), uniqueOrcidRule(i)]"
              :hint="Definitions.contributorOrcid"
              :disabled="currentUserOrcid === contributor.orcid"
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
          <div class="d-flex">
            <v-select
              v-model="contributor.roles"
              :rules="[v => v.length >= 1 || 'At least one role is required']"
              :items="NmdcSchema.$defs.CreditEnum.enum"
              label="CRediT Roles *"
              :hint="Definitions.contributorRoles"
              deletable-chips
              multiple
              outlined
              chips
              small-chips
              dense
              persistent-hint
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
              outlined
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
