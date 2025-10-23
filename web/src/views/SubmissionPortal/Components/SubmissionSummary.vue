<script lang="ts">
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
import {
  computed,
  defineComponent,
  ref,
} from '@vue/composition-api';
import {
  validForms,
  canEditSubmissionMetadata,
  isOwner,
  studyForm,
  multiOmicsForm,
  checkDoiFormat,
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

    const panels = ref([]);

    const studyFormContent = computed(() => {
      if (validForms.studyFormValid) {
        return ['No changes needed.'];
      }
      const missingReqs: Array<string> = [];
      if (studyForm.studyName === null || studyForm.studyName.length < 8) {
        missingReqs.push('Study name is required and must be 8 or more characters long.');
      }
      if (studyForm.piEmail === null || /.+@.+\..+/.test(studyForm.piEmail) === false) {
        missingReqs.push('A PI email is required, and must be formatted correctly.');
      }
      let fundingInvalid = false;
      if (studyForm.fundingSources != null && studyForm.fundingSources.length > 0) {
        studyForm.fundingSources.forEach((source) => {
          if (source === null || source.length === 0) {
            fundingInvalid = true;
          }
        });
      }
      if (fundingInvalid) {
        missingReqs.push('One or more funding sources is incomplete.');
      }

      let contributorsInvalid = false;
      if (studyForm.contributors != null && studyForm.contributors.length > 0) {
        studyForm.contributors.forEach((contributor) => {
          if (contributor.name === null || contributor.roles.length === 0) {
            contributorsInvalid = true;
          }
        });
      }
      if (contributorsInvalid) {
        missingReqs.push('One or more contributors is incomplete.');
      }

      let doisInvalid = false;
      if (studyForm.dataDois != null && studyForm.dataDois.length > 0) {
        studyForm.dataDois.forEach((doi) => {
          if (doi.provider === null || doi.value === null || checkDoiFormat(doi.value) === false) {
            doisInvalid = true;
          }
        });
      }
      if (doisInvalid) {
        missingReqs.push('One or more data DOIs is incomplete.');
      }
      return missingReqs;
    });

    const multiOmicsContent = computed(() => {
      if (validForms.multiOmicsFormValid) {
        return ['No changes needed.'];
      }
      if (multiOmicsForm.dataGenerated === null) {
        return ['Select whether or not data has been generated to determine requirements.'];
      }
      const missingReqs: Array<string> = [];
      if (multiOmicsForm.dataGenerated === false && multiOmicsForm.doe && multiOmicsForm.facilities != null && multiOmicsForm.facilities.length > 0 && multiOmicsForm.award === null) {
        missingReqs.push('You must select the kind of project you have been awarded');
      }
      if (multiOmicsForm.doe === null) {
        missingReqs.push('You must select whether or not you are submitting data to a DOE facility.');
      }

      if (multiOmicsForm.facilities.includes('EMSL')) {
        if (/^\d{5}$/.test(multiOmicsForm.studyNumber) === false) {
          missingReqs.push('You must include a valid EMSL study ID when EMSL is selected.');
        }

        if (multiOmicsForm.dataGenerated === false && multiOmicsForm.ship == null) {
          missingReqs.push('You must select whether or not samples will be shipped.');
        }

        if (multiOmicsForm.dataGenerated === false && multiOmicsForm.ship === true && validForms.addressFormValid === false) {
          missingReqs.push('You must fill out the address form for shipping.');
        }
      }

      if (multiOmicsForm.facilities.includes('JGI') && /^\d{6}$/.test(multiOmicsForm.JGIStudyId) === false) {
        missingReqs.push('You must include a valid JGI study ID when JGI is selected.');
      }

      let doisInvalid = false;
      if (multiOmicsForm.awardDois != null && multiOmicsForm.awardDois.length > 0 && multiOmicsForm.unknownDoi === false) {
        multiOmicsForm.awardDois.forEach((doi) => {
          if (doi.provider === null || doi.value === null || checkDoiFormat(doi.value) === false) {
            doisInvalid = true;
          }
        });
      }
      if (doisInvalid) {
        missingReqs.push('One or more award DOIs is incomplete.');
      }

      return missingReqs;
    });

    const harmonizerContent = computed(() => {
      if (validForms.templatesValid) {
        return 'Validate and correct any errors in your harmonizer data.';
      }
      return 'You must select one or more templates in the sample environment tab.';
    });

    return {
      validForms,
      NmdcSchema,
      textVal,
      canSubmit,
      panels,
      studyFormContent,
      multiOmicsContent,
      harmonizerContent,
      canEditSubmissionMetadata,
      createNewStudyID,
    };
  },
});
</script>

<template>
  <div>
    <v-container>
      <div class="text-h2">
        Submission Summary
      </div>
      <div class="text-h5">
        Status and links to each portion of your submission. You may also link this submission to an existing study, or create a new study ID here.
      </div>
      <submission-permission-banner
        v-if="!canEditSubmissionMetadata()"
      />
      <v-expansion-panels
        model="panels"
        multiple
      >
        <v-expansion-panel>
          <v-expansion-panel-header disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Study Form Status
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
            <template #actions>
              <v-icon
                :color="validForms.studyFormValid ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.studyFormValid ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-list>
              <v-list-item
                v-for="(item, i) in studyFormContent"
                :key="i"
                :value="item"
              >
                <v-list-item-icon>
                  <v-icon> mdi-circle-small </v-icon>
                </v-list-item-icon>
                {{ item }}
              </v-list-item>
            </v-list>
          </v-expansion-panel-content>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-header disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Multi-Omics Form Status
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
            <template #actions>
              <v-icon
                :color="validForms.multiOmicsFormValid ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.multiOmicsFormValid ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-list>
              <v-list-item
                v-for="(item, i) in multiOmicsContent"
                :key="i"
                :value="item"
              >
                <v-list-item-icon>
                  <v-icon> mdi-circle-small </v-icon>
                </v-list-item-icon>
                {{ item }}
              </v-list-item>
            </v-list>
          </v-expansion-panel-content>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-header disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Sample Environment/Template status
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
            <template #actions>
              <v-icon
                :color="validForms.templatesValid ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.templatesValid ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            {{ validForms.templatesValid ? 'No changes needed.' : 'You must select one or more templates.' }}
          </v-expansion-panel-content>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-header disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Data Harmonizer Status
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
            <template #actions>
              <v-icon
                :color="validForms.harmonizerValid ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.harmonizerValid ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            {{ harmonizerContent }}
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
      <div class="text-h5 pt-5">
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
    </v-container>
  </div>
</template>
