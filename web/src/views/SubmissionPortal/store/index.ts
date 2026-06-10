import { chunk, cloneDeep, isEqual } from 'lodash';
import { defineStore } from 'pinia';
import { computed, reactive, watch } from 'vue';
import * as api from '@/views/SubmissionPortal/store/api.ts';
import { setSubmissionImage } from '@/views/SubmissionPortal/store/api.ts';
import {
  DATA_MG,
  DATA_MG_INTERLEAVED,
  DATA_MT,
  DATA_MT_INTERLEAVED,
  EMSL,
  HARMONIZER_TEMPLATES,
  JGI_MG,
  JGI_MG_LR,
  JGI_MT,
  MetadataSuggestion, MetadataSuggestionRequest,
  MultiOmicsForm,
  SampleData,
  SampleEnvironmentForm,
  SenderShippingInfoForm,
  StudyForm,
  SubmissionEditorRole,
  SubmissionImageType,
  SubmissionMetadata,
  SubmissionMetadataPatch,
  SubmissionSampleSet,
  SubmissionSampleSetPatch, SubmissionStatusEnum,
  SuggestionsMode,
  SuggestionType,
  TemplateName,
  UneditableReason,
} from '@/views/SubmissionPortal/types.ts';
import useRequest from '@/use/useRequest.ts';
import axios from 'axios';
import { stateRefs } from '@/store';
import { getPendingSuggestions, setPendingSuggestions } from '@/store/localStorage.ts';
import HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi.ts';

/* FORM DEFAULTS */
const studyFormDefault: StudyForm = {
  studyName: '',
  piName: '',
  piEmail: '',
  piOrcid: '',
  linkOutWebpage: [],
  studyDate: null,
  dataDois: [],
  publicationDois: [],
  fundingSources: [],
  description: '',
  notes: '',
  contributors: [],
  alternativeNames: [],
  GOLDStudyId: '',
  NCBIBioProjectId: '',
  validation: null,
};

const multiOmicsFormDefault: MultiOmicsForm = {
  award: null,
  awardDois: [],
  dataGenerated: null,
  doe: null,
  facilities: [],
  facilityGenerated: null,
  JGIStudyId: '',
  mgCompatible: null,
  mgInterleaved: null,
  mtCompatible: null,
  mtInterleaved: null,
  omicsProcessingTypes: [],
  otherAward: null,
  ship: null,
  studyNumber: '',
  unknownDoi: null,
  mpProtocols: null,
  mbProtocols: null,
  mbGcProtocols: null,
  lipProtocols: null,
  nomProtocols: null,
  nomLcProtocols: null,
  validation: null,
};

const sampleEnvironmentFormDefault: SampleEnvironmentForm = {
  validation: null,
  packageName: [],
};

const senderShippingInfoFormDefault: SenderShippingInfoForm = {
  shipper: {
    name: '',
    email: '',
    phone: '',
    line1: '',
    line2: '',
    city: '',
    state: '',
    postalCode: '',
    country: '',
  },
  expectedShippingDate: null,
  shippingConditions: '',
  sample: '',
  description: '',
  experimentalGoals: '',
  randomization: '',
  usdaRegulated: null,
  permitNumber: '',
  biosafetyLevel: '',
  irbOrHipaa: null,
  comments: '',
  validation: null,
};

const sampleDataDefault: SampleData = {
  data: {},
  validation: null,
};

/* STORE TYPES */
type SubmissionForms = {
  studyForm: StudyForm;
};

type SampleSetForms = {
  multiOmicsForm: MultiOmicsForm
  sampleEnvironmentForm: SampleEnvironmentForm;
  senderShippingInfoForm: SenderShippingInfoForm;
  sampleData: SampleData;
}

type SubmissionStoreState = {
  record: SubmissionMetadata | null;
  permissionLevel: SubmissionEditorRole | null;
  forms: SubmissionForms;
  lastSavedForms: SubmissionForms;
  requests: {
    loading: ReturnType<typeof useRequest>;
    saving: ReturnType<typeof useRequest>;
  }
};

type SampleSetStoreState = {
  record: SubmissionSampleSet | null;
  forms: SampleSetForms;
  lastSavedForms: SampleSetForms;
  suggestions: MetadataSuggestion[];
  requests: {
    loading: ReturnType<typeof useRequest>;
    saving: ReturnType<typeof useRequest>;
    loadingSuggestions: ReturnType<typeof useRequest>;
  }
}

type UiState = {
  suggestionMode: SuggestionsMode
  suggestionType: SuggestionType
}

/* STATE-FREE HELPERS */
function createEmptySubmissionForms(): SubmissionForms {
  return {
    studyForm: cloneDeep(studyFormDefault),
  };
}

function createEmptySampleSetForms(): SampleSetForms {
  return {
    multiOmicsForm: cloneDeep(multiOmicsFormDefault),
    sampleEnvironmentForm: cloneDeep(sampleEnvironmentFormDefault),
    senderShippingInfoForm: cloneDeep(senderShippingInfoFormDefault),
    sampleData: cloneDeep(sampleDataDefault),
  }
}

export const useSubmissionStore = defineStore('submission', () => {
  /* STATE */
  const submission = reactive<SubmissionStoreState>({
    record: null,
    permissionLevel: null,
    forms: createEmptySubmissionForms(),
    lastSavedForms: createEmptySubmissionForms(),
    requests: {
      loading: useRequest(),
      saving: useRequest(),
    },
  });
  const sampleSet = reactive<SampleSetStoreState>({
    record: null,
    forms: createEmptySampleSetForms(),
    lastSavedForms: createEmptySampleSetForms(),
    suggestions: [],
    requests: {
      loading: useRequest(),
      saving: useRequest(),
      loadingSuggestions: useRequest(),
    },
  });
  const ui = reactive<UiState>({
    suggestionMode: SuggestionsMode.LIVE,
    suggestionType: SuggestionType.ALL,
  });

  /* GETTERS */
  const studyName = computed(() => submission.record?.study_name ?? '');
  const isOwner = computed(() => submission.permissionLevel === 'owner');
  const submissionIsDirty = computed(() => !isEqual(submission.forms, submission.lastSavedForms));
  const sampleSetIsDirty = computed(() => !isEqual(sampleSet.forms, sampleSet.lastSavedForms));
  const templateList = computed<TemplateName[]>((prevTemplates) => {
    const { multiOmicsForm, sampleEnvironmentForm } = sampleSet.forms;
    const templates = new Set(sampleEnvironmentForm.packageName);
    if (multiOmicsForm.dataGenerated) {
      // Have data already been generated? Yes
      if (!multiOmicsForm.doe) {
        // Were the data generated at a DOE facility? No
        if (multiOmicsForm.omicsProcessingTypes.includes('mg')) {
          // Which datatypes were generated? Metagenome
          if (multiOmicsForm.mgCompatible) {
            // Is the generated data compatible? Yes
            if (multiOmicsForm.mgInterleaved) {
              // Is the generated data interleaved? Yes
              templates.add(DATA_MG_INTERLEAVED);
            } else {
              // Is the generated data interleaved? No
              templates.add(DATA_MG);
            }
          }
        }
        if (multiOmicsForm.omicsProcessingTypes.includes('mt')) {
          // Which datatypes were generated? Metatranscriptome
          if (multiOmicsForm.mtCompatible) {
            // Is the generated data compatible? Yes
            if (multiOmicsForm.mtInterleaved) {
              // Is the generated data interleaved? Yes
              templates.add(DATA_MT_INTERLEAVED);
            } else {
              // Is the generated data interleaved? No
              templates.add(DATA_MT);
            }
          }
        }
      }
    } else {
      // Have data already been generated? No
      if (multiOmicsForm.doe) {
        // Are you submitting samples to a DOE user facility? Yes
        if (multiOmicsForm.facilities?.includes('EMSL')) {
          // Which facility? EMSL
          if (multiOmicsForm.omicsProcessingTypes.includes('lipidome-emsl')) {
            // Data types? Lipidome
            templates.add(EMSL);
          }
          if (multiOmicsForm.omicsProcessingTypes.includes('mp-emsl')) {
            // Data types? Metaproteome
            templates.add(EMSL);
          }
          if (multiOmicsForm.omicsProcessingTypes.includes('mb-emsl')) {
            // Data types? Metabolome
            templates.add(EMSL);
          }
          if (multiOmicsForm.omicsProcessingTypes.includes('nom-emsl')) {
            // Data types? Natural Organic Matter
            templates.add(EMSL);
          }
        }
        if (multiOmicsForm.facilities?.includes('JGI')) {
          // Which facility? JGI
          if (multiOmicsForm.omicsProcessingTypes.includes('mg-jgi')) {
            // Data types? Metagenome
            templates.add(JGI_MG);
          }
          if (multiOmicsForm.omicsProcessingTypes.includes('mg-lr-jgi')) {
            // Data types? Metagenome Long Read
            templates.add(JGI_MG_LR);
          }
          if (multiOmicsForm.omicsProcessingTypes.includes('mt-jgi')) {
            // Data types? Metatranscriptome
            templates.add(JGI_MT);
          }
        }
      }
    }
    const newTemplates = Array.from(templates);
    if (prevTemplates !== undefined && isEqual(prevTemplates, newTemplates)) {
      return prevTemplates;
    }
    return newTemplates;
  });

  /* WATCHERS */
  // When "Have data already been generated for your study?" changes, reset the answers to dependent questions
  watch(() => sampleSet.forms.multiOmicsForm.dataGenerated, (newValue, prevValue) => {
    // The answer was reset or changed from "No" to "Yes"
    // Reset "Are you submitting samples to a DOE user facility (JGI, EMSL)?"
    if (newValue === null || (prevValue === false && newValue === true)) {
      sampleSet.forms.multiOmicsForm.doe = null;
    }
    // The answer was reset or changed from "Yes" to "No"
    // Reset "Was data generated at a DOE user facility (JGI, EMSL)?"
    if (newValue === null || (prevValue === true && newValue === false)) {
      sampleSet.forms.multiOmicsForm.facilityGenerated = null;
    }
  });

  // When "Was data generated at a DOE user facility?" changes, reset the answers to dependent questions
  watch(() => sampleSet.forms.multiOmicsForm.facilityGenerated, (newValue, prevValue) => {
    // The answer was reset or changed from "No" to "Yes"
    // Uncheck all "Which facility?" checkboxes
    if (newValue === null || (prevValue === false && newValue === true)) {
      sampleSet.forms.multiOmicsForm.omicsProcessingTypes = [];
    }
    // The answer was reset or changed from "Yes" to "No"
    // Uncheck all "Which data types were generated?" checkboxes
    if (newValue === null || (prevValue === true && newValue === false)) {
      sampleSet.forms.multiOmicsForm.facilities = [];
      sampleSet.forms.multiOmicsForm.awardDois = []
    }
  });

  // When "Are you submitting samples to a DOE user facility?" changes, reset the answers to dependent questions
  watch(() => sampleSet.forms.multiOmicsForm.doe, ( newValue, prevValue) => {
    // The answer was reset or changed from "No" to "Yes"
    if (newValue === null || (prevValue === false && newValue === true)) {
      sampleSet.forms.multiOmicsForm.omicsProcessingTypes = [];
    }
    // The answer was reset or changed from "Yes" to "No"
    if (newValue === null || (prevValue === true && newValue === false)) {
      sampleSet.forms.multiOmicsForm.award = null;
      sampleSet.forms.multiOmicsForm.otherAward = null;
      sampleSet.forms.multiOmicsForm.facilities = [];
      sampleSet.forms.multiOmicsForm.awardDois = [];
    }
  });

  // When "Which facility?" changes, reset the answers to dependent questions
  watch(() => sampleSet.forms.multiOmicsForm.facilities, (newValue, prevValue) => {
    const newArray = newValue || [];
    const prevArray = prevValue || [];
    // EMSL was removed
    if (!newArray.includes('EMSL') && prevArray.includes('EMSL')) {
      sampleSet.forms.multiOmicsForm.studyNumber = '';
      sampleSet.forms.multiOmicsForm.ship = null;
      sampleSet.forms.multiOmicsForm.omicsProcessingTypes = sampleSet.forms.multiOmicsForm.omicsProcessingTypes.filter(t => (
        t !== 'lipidome-emsl' && t !== 'mp-emsl' && t !== 'mb-emsl' && t !== 'nom-emsl'
      ));
    }
    // JGI was removed
    if (!newArray.includes('JGI') && prevArray.includes('JGI')) {
      sampleSet.forms.multiOmicsForm.JGIStudyId = '';
      sampleSet.forms.multiOmicsForm.omicsProcessingTypes = sampleSet.forms.multiOmicsForm.omicsProcessingTypes.filter(t => (
        t !== 'mg-jgi' && t !== 'mg-lr-jgi' && t !== 'mt-jgi' && t !== 'mb-jgi'
      ));
    }
  });

  // When "Which data types were generated?" changes, reset the answers to dependent questions
  watch(() => sampleSet.forms.multiOmicsForm.omicsProcessingTypes, (newValue, oldValue) => {
    // mg was removed
    if (!newValue.includes('mg') && oldValue.includes('mg')) {
      sampleSet.forms.multiOmicsForm.mgCompatible = null;
    }
    // mt was removed
    if (!newValue.includes('mt') && oldValue.includes('mt')) {
      sampleSet.forms.multiOmicsForm.mtCompatible = null;
    }
    // mp was removed
    if (!newValue.includes('mp') && oldValue.includes('mp')) {
      sampleSet.forms.multiOmicsForm.mpProtocols = null;
    }
    // mb was removed
    if (!newValue.includes('mb') && oldValue.includes('mb')) {
      sampleSet.forms.multiOmicsForm.mbProtocols = null;
    }
    // mb-gc was removed
    if (!newValue.includes('mb-gc') && oldValue.includes('mb-gc')) {
      sampleSet.forms.multiOmicsForm.mbGcProtocols = null;
    }
    // nom was removed
    if (!newValue.includes('nom') && oldValue.includes('nom')) {
      sampleSet.forms.multiOmicsForm.nomProtocols = null;
    }
    // nom-lc was removed
    if (!newValue.includes('nom-lc') && oldValue.includes('nom-lc')) {
      sampleSet.forms.multiOmicsForm.nomLcProtocols = null;
    }
    // lipidome was removed
    if (!newValue.includes('lipidome') && oldValue.includes('lipidome')) {
      sampleSet.forms.multiOmicsForm.lipProtocols = null;
    }
  });

  // When "Is the generated data compatible?" changes for either mg or mt, reset the answers to dependent questions
  watch(() => sampleSet.forms.multiOmicsForm.mgCompatible, (newValue, oldValue) => {
    // mg compatible was cleared or changed from true to false
    if (newValue === null || (newValue === false && oldValue === true)) {
      sampleSet.forms.multiOmicsForm.mgInterleaved = null;
    }
  });
  watch(() => sampleSet.forms.multiOmicsForm.mtCompatible, (newValue, oldValue) => {
    // mt compatible was cleared or changed from true to false
    if (newValue === null || (newValue === false && oldValue === true)) {
      sampleSet.forms.multiOmicsForm.mtInterleaved = null;
    }
  });

  // Watch for changes to the "Will samples be shipped?" field. If the field is reset or the answer becomes "No",
  // reset the sender shipping info form validation state to null (untouched).
  watch(() => sampleSet.forms.multiOmicsForm.ship, (newVal) => {
    if (newVal !== true) {
      sampleSet.forms.senderShippingInfoForm.validation = null;
    }
  });


  /* HELPERS */
  /**
   * Populate the submission state with data from the server.
   *
   * This is used after loading a submission and after saving edits to ensure the state is in sync with the server. If
   * the response does not include certain fields (e.g. permission_level), those fields will not be updated in the state
   * to avoid accidentally overwriting existing values with null.
   * @param data
   */
  function hydrateSubmission(data: SubmissionMetadata | null) {
    if (data === null) {
      return;
    }
    submission.record = data;
    // The permission_level field is only included on the response when fetching a single submission.
    // It is not populated on other operations like updating a submission. So only update the state
    // if the field is included in the response.
    if (data.permission_level !== null) {
      submission.permissionLevel = data.permission_level;
    }

    const forms: SubmissionForms = {
      studyForm: cloneDeep(data.study_form),
    }
    submission.forms = forms;
    submission.lastSavedForms = cloneDeep(forms);
  }

  /**
   * Populate the sample set state with data from the server.
   *
   * This is used after loading a sample set and after saving edits to ensure the state is in sync with the server.
   *
   * @param data
   */
  function hydrateSampleSet(data: SubmissionSampleSet | null) {
    if (data === null) {
      return;
    }
    sampleSet.record = data;

    const forms: SampleSetForms = {
      multiOmicsForm: cloneDeep(data.multi_omics_form),
      sampleEnvironmentForm: cloneDeep(data.sample_environment_form),
      senderShippingInfoForm: cloneDeep(data.sender_shipping_info_form),
      sampleData: cloneDeep(data.sample_data),
    }
    sampleSet.forms = forms;
    sampleSet.lastSavedForms = cloneDeep(forms);
  }

  /* ACTIONS */
  /**
   * Load a submission from the server and populate the state
   *
   * @param id
   */
  async function loadSubmission(id: string) {
    const response = await submission.requests.loading.request(
      () => api.getSubmission(id)
    );
    hydrateSubmission(response);
  }

  /**
   * Create a new submission on the server and populate the state with the response.
   *
   * The new submission will be initialized with default values for the forms, overridden by the provided arguments.
   *
   * @param studyName
   * @param piEmail
   * @param isTestSubmission
   */
  async function createSubmission(studyName: string, piEmail: string, isTestSubmission: boolean) {
    const response = await submission.requests.saving.request(
      () => api.createSubmission({
        study_form: {
          ...studyFormDefault,
          piEmail,
          studyName,
        },
        is_test_submission: isTestSubmission,
        source_client: 'submission_portal',
      })
    );
    hydrateSubmission(response);
    return response;
  }

  /**
   * Save active edits to the submission forms by sending a PATCH request to the server.
   *
   * If the user does not have permission to edit, or if there are no changes to save, this function will return early
   * without making an API request. Only if the user has owner permissions, the API request will include the permissions
   * object to update submission roles.
   */
  async function saveSubmissionFormEdits() {
    if (submission.record === null) {
      throw new Error('No submission loaded');
    }

    if (getSubmissionUneditableReason(['owner', 'editor']) !== undefined) {
      return;
    }

    if (!submissionIsDirty.value) {
      return;
    }

    let payload: SubmissionMetadataPatch;
    if (isOwner.value) {
      const permissions: Record<string, SubmissionEditorRole> = {};
      submission.forms.studyForm.contributors.forEach((contributor) => {
        const { orcid, permissionLevel } = contributor;
        if (orcid && permissionLevel) {
          permissions[orcid] = permissionLevel;
        }
      });
      // This should happen last to ensure the PI is an owner
      if (submission.forms.studyForm.piOrcid) {
        permissions[submission.forms.studyForm.piOrcid] = 'owner';
      }
      payload = {
        study_form: submission.forms.studyForm,
        permissions,
      }
    } else {
      payload = {
        study_form: submission.forms.studyForm,
      }
    }

    const response = await submission.requests.saving.request(
      () => api.updateSubmission(submission.record!.id, payload)
    )
    hydrateSubmission(response);
  }

  /**
   * Upload an image file for the submission
   *
   * The upload process involves three steps:
   * 1. Requesting a signed URL from the backend for the file to be uploaded to GCS
   * 2. Uploading the file directly to GCS using the signed URL
   * 3. Notifying the backend that the upload is complete so it can update the submission record with the stored object
   *    name.
   * @param file
   * @param imageType
   */
  async function uploadSubmissionImage(file: File, imageType: SubmissionImageType) {
    if (submission.record === null) {
      throw new Error('No submission loaded');
    }
    // First, get a signed URL from the backend
    const submissionId = submission.record.id
    const signedUrlResponse = await api.generateSignedUploadUrl(submissionId, file);

    // Next, upload the file to the signed URL
    const uploadResponse = await fetch(signedUrlResponse.url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
      },
      body: file,
    });

    // Finally, if the upload was successful, notify the backend so it can update the submission record with the stored
    // object name
    if (uploadResponse.ok) {
      submission.record = await setSubmissionImage(submissionId, file, signedUrlResponse.object_name, imageType);
    } else {
      throw new Error('File upload failed');
    }
  }

  /**
   * Delete an image associated with the submission.
   *
   * @param imageType
   */
  async function deleteSubmissionImage(imageType: SubmissionImageType) {
    if (submission.record === null) {
      throw new Error('No submission loaded');
    }
    const submissionId = submission.record.id;
    submission.record = await api.deleteSubmissionImage(submissionId, imageType);
  }

  /**
   * Request the edit lock on the submission.
   *
   * If the lock is successfully acquired or if it cannot be acquired because the current user already has the lock, the
   * submission record in the state will be updated with the lock information provided by the server.
   *
   * @param submissionId
   */
  async function lockSubmission(submissionId: string) {
    if (submission.record === null) {
      throw new Error('No submission loaded');
    }
    if (submissionId !== submission.record?.id) {
      throw new Error('Can only lock the currently loaded submission');
    }
    try {
      const lockResponse = await api.lockSubmission(submissionId);
      submission.record.locked_by = lockResponse.locked_by;
      submission.record.lock_updated = lockResponse.lock_updated;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response && error.response.status === 409) {
          // Another user has the lock
          submission.record.locked_by = error.response.data.locked_by || null;
          submission.record.lock_updated = error.response.data.lock_updated || null;
        }
      } else {
        // Something went wrong, and we don't know who has the lock
        submission.record.locked_by = null;
        submission.record.lock_updated = null;
      }
    }
  }

  /**
   * Release the edit lock on the submission.
   *
   * @param submissionId
   */
  async function unlockSubmission(submissionId: string) {
    if (submission.record === null) {
      throw new Error('No submission loaded');
    }
    if (submissionId !== submission.record.id) {
      throw new Error('Can only unlock the currently loaded submission');
    }
    try {
      await api.unlockSubmission(submissionId);
      submission.record.locked_by = null;
      submission.record.lock_updated = null;
    } catch {
      // Ignore errors when unlocking
    }
  }

  /**
   * Determine if the submission is editable by the current user and return a reason if it is not editable.
   *
   * A submission is not editable if:
   * - It is locked by another user
   * - The current user does not have one of the specified roles
   *
   * @param allowedRoles
   */
  function getSubmissionUneditableReason(allowedRoles: SubmissionEditorRole[]): UneditableReason | undefined {
    if (submission.record === null) {
      return;
    }

    if (submission.record.locked_by !== null && submission.record.locked_by.orcid !== stateRefs.user.value?.orcid) {
      return 'locked_by_other';
    }

    if (submission.permissionLevel === null || !allowedRoles.includes(submission.permissionLevel)) {
      return 'insufficient_permissions';
    }
  }

  /**
   * Load a sample set from the server and populate the state
   *
   * @param sampleSetId
   */
  async function loadSampleSet(sampleSetId: string) {
    const response = await sampleSet.requests.loading.request(
      () => api.getSampleSet(sampleSetId)
    );
    hydrateSampleSet(response);
  }

  /**
   * Save active edits to the sample set forms by sending a PATCH request to the server.
   *
   * If the user does not have permission to edit or if there are no changes to save, this function will return early
   * without making an API request. Only if the user has owner or editor permissions, the API request will include the
   * multi-omics, sample environment and sender shipping info forms.
   */
  async function saveSampleSetFormEdits() {
    if (sampleSet.record === null) {
      throw new Error('No sample set loaded');
    }

    if (getSubmissionUneditableReason(['owner', 'editor', 'metadata_contributor']) !== undefined) {
      return;
    }

    if (!sampleSetIsDirty.value) {
      return;
    }

    const payload: SubmissionSampleSetPatch = {
      sample_data: sampleSet.forms.sampleData,
    }
    if (['owner', 'editor'].includes(submission.permissionLevel || '')) {
      payload.templates = templateList.value;
      payload.multi_omics_form = sampleSet.forms.multiOmicsForm;
      payload.sample_environment_form = sampleSet.forms.sampleEnvironmentForm;
      payload.sender_shipping_info_form = sampleSet.forms.senderShippingInfoForm;
    }

    const response = await sampleSet.requests.saving.request(
      () => api.updateSubmissionSampleSet(sampleSet.record!.id, payload)
    );
    hydrateSampleSet(response);
  }

  /**
   * Submit the sample set for review
   *
   * Only users with owner permissions can submit. First any active changes to the sample set forms will be saved, then
   * a request will be sent to update the sample set status to "Submitted - Pending Review".
   */
  async function submitSampleSet() {
    if (sampleSet.record === null) {
      throw new Error('No sample set loaded');
    }

    const uneditableReason = getSubmissionUneditableReason(['owner']);
    if (uneditableReason) {
      throw new Error(`Unable to submit: ${ uneditableReason }`);
    }
    await saveSampleSetFormEdits();
    const response = await sampleSet.requests.saving.request(
      () => api.updateSubmissionSampleSetStatus(sampleSet.record!.id, {
        status: SubmissionStatusEnum.SubmittedPendingReview.text,
      })
    )
    hydrateSampleSet(response);
  }

  /**
   * Determine if the sample data template(s) associated with the specified template name(s) contain any data.
   *
   * This is used to determine whether certain edits to the multi-omics form should be blocked to avoid orphaning
   * existing sample metadata.
   *
   * @param template
   */
  function templateHasData(template: TemplateName | TemplateName[] | "ANY"): boolean {
    // if DH hasn't been touched at all then there's no data, and it's ok edit
    if (Object.keys(sampleSet.forms.sampleData.data).length === 0) {
      return false;
    }

    // If the special "ANY" value is passed, check the existing sampleData for any template that contains data.
    if (template === 'ANY') {
      const templateWithDataIndex = Object.values(sampleSet.forms.sampleData.data)
        .findIndex((value) => value.length > 0);
      return templateWithDataIndex >= 0;
    }

    // If specific template(s) are passed, check if those templates contain data. When multiple
    // templates are passed, return true if any of the templates contain data.
    const templateNames: TemplateName[] = Array.isArray(template) ? template : [template];
    for (const templateName of templateNames) {
      const harmonizer_template = HARMONIZER_TEMPLATES[templateName];
      if (!("sampleDataSlot" in harmonizer_template)) {
        continue;
      }
      const slotName = harmonizer_template.sampleDataSlot;
      if (Object.values(sampleSet.forms.sampleData.data[slotName] || {}).length > 0) {
        return true;
      }
    }
    return false;
  }

  /**
   * Get metadata suggestions from the server and add them to the list of pending suggestions. Then sync the pending
   * suggestions with local storage.
   *
   * @param schemaClassName
   * @param requests
   * @param batchSize
   */
  async function loadSuggestionsFromSampleRows(schemaClassName: string, requests: MetadataSuggestionRequest[], batchSize: number = 10) {
    if (sampleSet.record === null) {
      throw new Error('No sample set loaded');
    }
    return sampleSet.requests.loadingSuggestions.request(async () => {
      const batches = chunk(requests, batchSize);
      for (let i = 0; i < batches.length; i += 1) {
        const batch = batches[i] || [];


        const suggestions = await api.getMetadataSuggestions(batch, ui.suggestionType);

        // Drop all the existing suggestions for the rows in this batch
        batch.forEach((request) => {
          sampleSet.suggestions = sampleSet.suggestions.filter(
            (suggestion) => suggestion.row !== request.row,
          );
        });

        // Add the new suggestions to the list
        sampleSet.suggestions.push(...suggestions);
      }

      setPendingSuggestions(sampleSet.record!.id, schemaClassName, sampleSet.suggestions);
    });
  }

  /**
   * Get suggestions from the server based on study information.
   *
   * These suggestions are not tied to specific submission schema classes, so this function needs to sort out which
   * classes the target slot is part of and then sync the pending suggestions with local storage. If there is an
   * existing suggestion for the same slot, row and type as an incoming suggestion, the existing suggestion will be
   * replaced by the incoming one. The in-memory list of suggestions will also be updated to trigger reactivity in the
   * UI if the active schema class is the one being updated.
   *
   * @param allSchemaClassNames
   * @param activeSchemaClassName
   * @param harmonizerApi
   */
  async function loadSuggestionsFromStudyInfo(allSchemaClassNames: string[], activeSchemaClassName: string, harmonizerApi: HarmonizerApi) {
    if (submission.record === null) {
      throw new Error('No submission loaded');
    }
    if (sampleSet.record === null) {
      throw new Error('No sample set loaded');
    }
    const submissionId = submission.record.id;
    const sampleSetId = sampleSet.record.id;
    return sampleSet.requests.loadingSuggestions.request(async () => {
      const suggestions = await api.getMetadataSuggestionsFromStudyDetails(submissionId);
      for (const schemaClassName of allSchemaClassNames) {
        const suggestionsForClass = getPendingSuggestions(sampleSetId, schemaClassName);
        suggestions.forEach((suggestion) => {
          if (!harmonizerApi.isSlotInClass(suggestion.slot, schemaClassName)) {
            return;
          }
          const existingIndex = suggestionsForClass.findIndex(
            (s) => s.row === suggestion.row && s.slot === suggestion.slot && s.type === suggestion.type,
          );
          if (existingIndex >= 0) {
            // Replace existing suggestion
            suggestionsForClass[existingIndex] = suggestion;
          } else {
            // Add new suggestion
            suggestionsForClass.push(suggestion);
          }
        });
        setPendingSuggestions(sampleSetId, schemaClassName, suggestionsForClass);
        if (schemaClassName === activeSchemaClassName) {
          // If the active schema class is the one we just updated, also update the in-memory list of suggestions to trigger reactivity
          sampleSet.suggestions = getPendingSuggestions(sampleSetId, schemaClassName);
        }
      }
    });
  }

  /**
   * Save active edits to both the submission and sample set forms
   */
  async function saveFormEdits() {
    if (submission.record !== null) {
      await saveSubmissionFormEdits();
    }
    if (sampleSet.record !== null) {
      await saveSampleSetFormEdits();
    }
  }

  return {
    /* STATE */
    submission,
    sampleSet,
    ui,

    /* GETTERS */
    studyName,
    isOwner,
    submissionIsDirty,
    sampleSetIsDirty,
    templateList,

    /* ACTIONS */
    loadSubmission,
    createSubmission,
    saveSubmissionFormEdits,
    uploadSubmissionImage,
    deleteSubmissionImage,
    lockSubmission,
    unlockSubmission,
    getSubmissionUneditableReason,
    loadSampleSet,
    saveSampleSetFormEdits,
    submitSampleSet,
    templateHasData,
    loadSuggestionsFromSampleRows,
    loadSuggestionsFromStudyInfo,
    saveFormEdits,
  }
});
