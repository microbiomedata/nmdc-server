import { computed, reactive, toRef, watch, } from 'vue';
import { chunk, clone, forEach, isEqual, isString, } from 'lodash';
import axios from 'axios';
import { User } from '@/types';
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
  MetadataSuggestion,
  MetadataSuggestionRequest,
  MultiOmicsForm,
  SampleData,
  SampleEnvironmentForm,
  SampleMetadataValidationState,
  SubmissionEditorRole,
  SubmissionPage,
  SubmissionMetadata,
  SubmissionMetadataPatch,
  SubmissionSampleSet,
  SubmissionSampleSetListItem,
  SenderShippingInfoForm,
  StudyForm,
  SubmissionStatusEnum,
  SubmissionStatusKey,
  SuggestionType,
  SuggestionsMode,
  UneditableReason, SubmissionSampleSetPatch,
} from '@/views/SubmissionPortal/types';
import { getPendingSuggestions, setPendingSuggestions } from '@/store/localStorage';
import * as api from './api';
import useRequest from '@/use/useRequest.ts';
import HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi.ts';
import { stateRefs } from '@/store';

const permissionLevelHierarchy: Record<SubmissionEditorRole, number> = {
  owner: 4,
  editor: 3,
  metadata_contributor: 2,
  reviewer: 1,
  viewer: 1,
};

function isOwner(): boolean {
  const permissionLevel = getCurrentPermissionLevel();
  if (!permissionLevel) {
    return false;
  }
  return permissionLevelHierarchy[permissionLevel] === permissionLevelHierarchy.owner;
}

function isStatusEditable(status: SubmissionStatusKey): boolean {
  const editableStatuses: SubmissionStatusKey[] = ['InProgress', 'UpdatesRequired'];
  return editableStatuses.includes(status);
}

async function editableByStatus(submissionId: string): Promise<boolean> {
  const editableStatuses: SubmissionStatusKey[] = ['InProgress', 'UpdatesRequired'];
  const sampleSets = await api.listSubmissionSampleSets(submissionId);
  return sampleSets.some((sampleSet: any) => editableStatuses.includes(sampleSet.status));
}

function canEditSubmissionByStatus(): boolean {
  return isStatusEditable(status.value);
}

/**
 * Check if the given permission level meets the minimum required permission level
 * @param permissionLevel
 * @param minimumPermissionLevel
 */
function hasMinimumPermissionLevel(permissionLevel: SubmissionEditorRole | null, minimumPermissionLevel: SubmissionEditorRole): boolean {
  return permissionLevel !== null && permissionLevelHierarchy[permissionLevel] >= permissionLevelHierarchy[minimumPermissionLevel];
}

function getCurrentPermissionLevel(): SubmissionEditorRole | null {
  return submissionState.submission?.permission_level as SubmissionEditorRole | null;
}

function getSubmissionUneditableReason(minimumPermissionLevel: SubmissionEditorRole): UneditableReason | undefined {
  if (!loggedInUserHasLock.value) {
    return 'locked_by_other';
  }

  if (!hasMinimumPermissionLevel(getCurrentPermissionLevel(), minimumPermissionLevel)) {
    return 'insufficient_permissions'
  }

  if (!canEditSubmissionByStatus()) {
    return 'uneditable_status'
  }

  return undefined;
}

/**
 * Validating forms
*/
function setTabValidated(tabName: string, validated: boolean) {
  if (sampleData.validation === null) {
      sampleData.validation = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  if (!templateList.value.includes(tabName)) {
    return;
  }
  sampleData.validation.tabsValidated[tabName] = validated;
}

function setTabInvalidCells(tabName: string, invalidCells: Record<number, Record<number, string>>) {
  if (sampleData.validation === null) {
    sampleData.validation = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  if (!templateList.value.includes(tabName)) {
    return;
  }
  sampleData.validation.invalidCells[tabName] = invalidCells;
}

function resetSampleMetadataValidation() {
  if (sampleData.validation === null) {
    sampleData.validation = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  sampleData.validation.invalidCells = {};
  Object.keys(sampleData.validation.tabsValidated).forEach((tab) => {
    sampleData.validation!.tabsValidated[tab] = false;
  });
}

function isSubmissionValid() {
  // The required forms must be validated with no errors
  if (!isEqual(studyForm.validation, [])) {
    return false;
  }
  if (!isEqual(multiOmicsForm.validation, [])) {
    return false;
  }
  if (!isEqual(sampleEnvironmentForm.validation, [])) {
    return false;
  }
  // The sender shipping info form is optional. If it has been validated, it must have no errors
  if (senderShippingInfoForm.validation != null && !isEqual(senderShippingInfoForm.validation, [])) {
    return false;
  }
  // The sample metadata must be validated with no errors
  if (sampleData.validation == null) {
    return false;
  }
  const tabsValidatedValues = Object.values(sampleData.validation.tabsValidated);
  if (tabsValidatedValues.length === 0) {
    return false;
  }
  if (tabsValidatedValues.some((validated) => !validated)) {
    return false;
  }
  if (Object.values(sampleData.validation.invalidCells).some((cells) => Object.keys(cells).length > 0)) {
    return false;
  }
  return true;
}

function combineErrors(...errorLists: (null | string[])[]) : null | string[] {
  let combined: null | string[] = null;
  errorLists.forEach((errors) => {
    if (errors) {
      if (combined === null) {
        combined = [];
      }
      combined = combined.concat(errors);
    }
  });
  return combined;
}

function combineSampleMetadataErrors(sampleMetadataState: SampleMetadataValidationState | null) : string[] | null {
  if (sampleMetadataState === null) {
    return null;
  }
  const combinedErrors: string[] = [];
  const tabsValidatedKeys = Object.keys(sampleMetadataState.tabsValidated);
  if (tabsValidatedKeys.length === 0) {
    combinedErrors.push('No tabs have been validated.');
  } else {
    tabsValidatedKeys.forEach((tab) => {
      let message = '';
      if (!sampleMetadataState.tabsValidated[tab]) {
        message = `Tab "${ tab }" has not been validated.`;
      }
      if (tab in sampleMetadataState.invalidCells) {
        const invalidCells = sampleMetadataState.invalidCells[tab];
        if (invalidCells && Object.keys(invalidCells).length > 0) {
          message = `Tab "${ tab }" has invalid cells.`;
        }
      }
      if (message) {
        combinedErrors.push(message);
      }
    })
  }
  return combinedErrors;
}

const submissionPages = computed<SubmissionPage[]>(() => ([
  {
    title: 'Study Information',
    link: { name: 'Study Form' },
    validationMessages: studyForm.validation,
  },
  {
    title: 'Multi-omics Data',
    link: { name: 'Multiomics Form' },
    validationMessages: combineErrors(multiOmicsForm.validation, senderShippingInfoForm.validation),
  },
  {
    title: 'Sample Environment',
    link: { name: 'Sample Environment' },
    validationMessages: sampleEnvironmentForm.validation,
  },
  {
    title: 'Sample Metadata',
    link: { name: 'Submission Sample Editor' },
    validationMessages: combineSampleMetadataErrors(sampleData.validation),
  },
]));

const senderShippingInfoFormDefault: SenderShippingInfoForm = {
  // Shipper info
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
  // Sample info
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

/**
 * Study Form Step
 */
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

/**
 * Multi-Omics Form Step
 */
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

/**
 * Environmental Package Step
 */
const sampleEnvironmentFormDefault: SampleEnvironmentForm = {
  validation: null,
  packageName: [],
};

function addAwardDoi() {
  if (!Array.isArray(multiOmicsForm.awardDois)) {
    multiOmicsForm.awardDois = [];
  }
  multiOmicsForm.awardDois.push({
    value: '',
    provider: '',
  });
}

function removeAwardDoi(i: number) {
  if (multiOmicsForm.awardDois === null) {
    multiOmicsForm.awardDois = [];
  }
  const facilityCount = multiOmicsForm.facilities?.length ?? 0;
  if ((facilityCount < multiOmicsForm.awardDois.length && !multiOmicsForm.dataGenerated) || (multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated && multiOmicsForm.awardDois.length > 1) || (!multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated)) {
    multiOmicsForm.awardDois.splice(i, 1);
  }
}

// When "Have data already been generated for your study?" changes, reset the answers to dependent questions
watch(() => multiOmicsForm.dataGenerated, (newValue, prevValue) => {
  // The answer was reset or changed from "No" to "Yes"
  // Reset "Are you submitting samples to a DOE user facility (JGI, EMSL)?"
  if (newValue === null || (prevValue === false && newValue === true)) {
    multiOmicsForm.doe = null;
  }
  // The answer was reset or changed from "Yes" to "No"
  // Reset "Was data generated at a DOE user facility (JGI, EMSL)?"
  if (newValue === null || (prevValue === true && newValue === false)) {
    multiOmicsForm.facilityGenerated = null;
  }
});

// When "Was data generated at a DOE user facility?" changes, reset the answers to dependent questions
watch(() => multiOmicsForm.facilityGenerated, (newValue, prevValue) => {
  // The answer was reset or changed from "No" to "Yes"
  // Uncheck all "Which facility?" checkboxes
  if (newValue === null || (prevValue === false && newValue === true)) {
    multiOmicsForm.omicsProcessingTypes = [];
  }
  // The answer was reset or changed from "Yes" to "No"
  // Uncheck all "Which data types were generated?" checkboxes
  if (newValue === null || (prevValue === true && newValue === false)) {
    multiOmicsForm.facilities = [];
    multiOmicsForm.awardDois = []
  }
});

// When "Are you submitting samples to a DOE user facility?" changes, reset the answers to dependent questions
watch(() => multiOmicsForm.doe, ( newValue, prevValue) => {
  // The answer was reset or changed from "No" to "Yes"
  if (newValue === null || (prevValue === false && newValue === true)) {
    multiOmicsForm.omicsProcessingTypes = [];
  }
  // The answer was reset or changed from "Yes" to "No"
  if (newValue === null || (prevValue === true && newValue === false)) {
    multiOmicsForm.award = null;
    multiOmicsForm.otherAward = null;
    multiOmicsForm.facilities = [];
    multiOmicsForm.awardDois = [];
  }
});

// When "Which facility?" changes, reset the answers to dependent questions
watch(() => multiOmicsForm.facilities, (newValue, prevValue) => {
  const nextFacilities = newValue ?? [];
  const previousFacilities = prevValue ?? [];
  // EMSL was removed
  if (!nextFacilities.includes('EMSL') && previousFacilities.includes('EMSL')) {
    multiOmicsForm.studyNumber = '';
    multiOmicsForm.ship = null;
    multiOmicsForm.omicsProcessingTypes = multiOmicsForm.omicsProcessingTypes.filter(t => (
      t !== 'lipidome-emsl' && t !== 'mp-emsl' && t !== 'mb-emsl' && t !== 'nom-emsl'
    ));
  }
  // JGI was removed
  if (!nextFacilities.includes('JGI') && previousFacilities.includes('JGI')) {
    multiOmicsForm.JGIStudyId = '';
    multiOmicsForm.omicsProcessingTypes = multiOmicsForm.omicsProcessingTypes.filter(t => (
      t !== 'mg-jgi' && t !== 'mg-lr-jgi' && t !== 'mt-jgi' && t !== 'mb-jgi'
    ));
  }
});

// When "Which data types were generated?" changes, reset the answers to dependent questions
watch(() => multiOmicsForm.omicsProcessingTypes, (newValue, oldValue) => {
  // mg was removed
  if (!newValue.includes('mg') && oldValue.includes('mg')) {
    multiOmicsForm.mgCompatible = null;
  }
  // mt was removed
  if (!newValue.includes('mt') && oldValue.includes('mt')) {
    multiOmicsForm.mtCompatible = null;
  }
  // mp was removed
  if (!newValue.includes('mp') && oldValue.includes('mp')) {
    multiOmicsForm.mpProtocols = null;
  }
  // mb was removed
  if (!newValue.includes('mb') && oldValue.includes('mb')) {
    multiOmicsForm.mbProtocols = null;
  }
  // mb-gc was removed
  if (!newValue.includes('mb-gc') && oldValue.includes('mb-gc')) {
    multiOmicsForm.mbGcProtocols = null;
  }
  // nom was removed
  if (!newValue.includes('nom') && oldValue.includes('nom')) {
    multiOmicsForm.nomProtocols = null;
  }
  // nom-lc was removed
  if (!newValue.includes('nom-lc') && oldValue.includes('nom-lc')) {
    multiOmicsForm.nomLcProtocols = null;
  }
  // lipidome was removed
  if (!newValue.includes('lipidome') && oldValue.includes('lipidome')) {
    multiOmicsForm.lipProtocols = null;
  }
});

// When "Is the generated data compatible?" changes for either mg or mt, reset the answers to dependent questions
watch(() => multiOmicsForm.mgCompatible, (newValue, oldValue) => {
  // mg compatible was cleared or changed from true to false
  if (newValue === null || (newValue === false && oldValue === true)) {
    multiOmicsForm.mgInterleaved = null;
  }
});
watch(() => multiOmicsForm.mtCompatible, (newValue, oldValue) => {
  // mt compatible was cleared or changed from true to false
  if (newValue === null || (newValue === false && oldValue === true)) {
    multiOmicsForm.mtInterleaved = null;
  }
});

// Watch for changes to the "Will samples be shipped?" field. If the field is reset or the answer becomes "No",
// reset the sender shipping info form validation state to null (untouched).
watch(() => multiOmicsForm.ship, (newVal) => {
  if (newVal !== true) {
    senderShippingInfoForm.validation = null;
  }
});

const templateList = computed<string[]>((prevTemplates) => {
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
/**
 * DataHarmonizer Step
 */
const sampleDataDefault = {
  data: {} as Record<string, any[]>,
  validation: null as SampleMetadataValidationState | null,
};

type SubmissionDraft = {
  studyForm: StudyForm;
};

type SampleSetDraft = {
  name: string;
  multiOmicsForm: MultiOmicsForm;
  sampleEnvironmentForm: SampleEnvironmentForm;
  senderShippingInfoForm: SenderShippingInfoForm;
  sampleData: SampleData;
};

function createEmptySubmissionDraft(): SubmissionDraft {
  return {
    studyForm: clone(studyFormDefault),
  };
}

function createEmptySampleSetDraft(): SampleSetDraft {
  return {
    name: '',
    multiOmicsForm: clone(multiOmicsFormDefault),
    sampleEnvironmentForm: clone(sampleEnvironmentFormDefault),
    senderShippingInfoForm: clone(senderShippingInfoFormDefault),
    sampleData: clone(sampleDataDefault),
  };
}

const submissionState = reactive({
  submission: null as SubmissionMetadata | null,
  draft: createEmptySubmissionDraft(),
});

const sampleSetsState = reactive({
  items: [] as SubmissionSampleSetListItem[],
  activeSampleSetId: null as string | null,
  activeSampleSet: null as SubmissionSampleSet | null,
  draft: createEmptySampleSetDraft(),
});

const uiState = reactive({
  hasChanged: 0,
  metadataSuggestions: [] as MetadataSuggestion[],
  suggestionMode: SuggestionsMode.LIVE,
  suggestionType: SuggestionType.ALL,
});

const studyForm = submissionState.draft.studyForm;
const multiOmicsForm = sampleSetsState.draft.multiOmicsForm;
const sampleEnvironmentForm = sampleSetsState.draft.sampleEnvironmentForm;
const senderShippingInfoForm = sampleSetsState.draft.senderShippingInfoForm;
const sampleData = sampleSetsState.draft.sampleData;

const hasChanged = toRef(uiState, 'hasChanged');
const metadataSuggestions = toRef(uiState, 'metadataSuggestions');
const suggestionMode = toRef(uiState, 'suggestionMode');
const suggestionType = toRef(uiState, 'suggestionType');

const status = computed<SubmissionStatusKey>(() => {
  const sampleSetStatus = sampleSetsState.activeSampleSet?.status;
  if (sampleSetStatus && isStatusEditable(sampleSetStatus as SubmissionStatusKey)) {
    return sampleSetStatus as SubmissionStatusKey;
  }
  return 'InProgress';
});
const studyName = computed(() => submissionState.submission?.study_name ?? '');
const createdDate = computed(() => (
  submissionState.submission ? new Date(submissionState.submission.created + 'Z') : null
));
const modifiedDate = computed(() => (
  submissionState.submission ? new Date(submissionState.submission.date_last_modified + 'Z') : null
));
const isTestSubmission = computed(() => submissionState.submission?.is_test_submission ?? false);
const primaryStudyImageUrl = computed(() => submissionState.submission?.primary_study_image_url ?? null);
const piImageUrl = computed(() => submissionState.submission?.pi_image_url ?? null);
const author = computed<User | null>(() => submissionState.submission?.author ?? null);
const submissionLockedBy = computed<User | null>(() => submissionState.submission?.locked_by ?? null);

const statusDisplay = computed(() => SubmissionStatusEnum[status.value].title);

const loggedInUserHasLock = computed(() => {
  const lockedByUser = submissionLockedBy.value;
  if (!lockedByUser) {
    return true;
  }
  if (lockedByUser.orcid === stateRefs.user.value?.orcid) {
    return true;
  }
  return false;
});

const activeSampleSet = computed(() => sampleSetsState.activeSampleSet);
const sampleSetList = computed(() => sampleSetsState.items);
const activeSampleSetId = toRef(sampleSetsState, 'activeSampleSetId');

function resetSubmissionState() {
  Object.assign(submissionState.draft.studyForm, clone(studyFormDefault));
  submissionState.submission = null;
}

function resetActiveSampleSetDraft() {
  const emptyDraft = createEmptySampleSetDraft();
  Object.assign(sampleSetsState.draft, emptyDraft);
  Object.assign(sampleSetsState.draft.multiOmicsForm, emptyDraft.multiOmicsForm);
  Object.assign(sampleSetsState.draft.sampleEnvironmentForm, emptyDraft.sampleEnvironmentForm);
  Object.assign(sampleSetsState.draft.senderShippingInfoForm, emptyDraft.senderShippingInfoForm);
  Object.assign(sampleSetsState.draft.sampleData, emptyDraft.sampleData);
}

function resetSampleSetsState() {
  sampleSetsState.items = [];
  sampleSetsState.activeSampleSetId = null;
  sampleSetsState.activeSampleSet = null;
  resetActiveSampleSetDraft();
}

function resetStore() {
  resetSubmissionState();
  resetSampleSetsState();
  uiState.hasChanged = 0;
}

function hydrateSubmission(submission: SubmissionMetadata) {
  submissionState.submission = submission;
  Object.assign(submissionState.draft.studyForm, clone(submission.study_form));
}

async function saveActiveSampleSet(): Promise<SubmissionSampleSet | null> {
  const activeSampleSetId = sampleSetsState.activeSampleSetId;
  if (!activeSampleSetId) {
    return null;
  }

  const sampleSetPayload: SubmissionSampleSetPatch = {
    name: sampleSetsState.draft.name,
    templates: templateList.value,
    multi_omics_form: sampleSetsState.draft.multiOmicsForm,
    sample_environment_form: sampleSetsState.draft.sampleEnvironmentForm,
    sender_shipping_info_form: sampleSetsState.draft.senderShippingInfoForm,
    sample_data: sampleSetsState.draft.sampleData,
  };
  const sampleSet = await api.updateSubmissionSampleSet(activeSampleSetId, sampleSetPayload);
  hydrateActiveSampleSet(sampleSet);
  return sampleSet;
}

function hydrateSampleSetList(sampleSets: SubmissionSampleSetListItem[]) {
  sampleSetsState.items = sampleSets;
}

function hydrateActiveSampleSet(sampleSet: SubmissionSampleSet | null) {
  sampleSetsState.activeSampleSet = sampleSet;
  sampleSetsState.activeSampleSetId = sampleSet?.id ?? null;

  if (!sampleSet) {
    resetActiveSampleSetDraft();
    return;
  }

  sampleSetsState.draft.name = sampleSet.name;
  Object.assign(sampleSetsState.draft.multiOmicsForm, clone(sampleSet.multi_omics_form));
  Object.assign(sampleSetsState.draft.sampleEnvironmentForm, clone(sampleSet.sample_environment_form));
  Object.assign(sampleSetsState.draft.senderShippingInfoForm, clone(sampleSet.sender_shipping_info_form));
  Object.assign(sampleSetsState.draft.sampleData, clone(sampleSet.sample_data));
}

async function loadSubmissionSampleSets(submissionId: string) {
  const sampleSets = await api.listSubmissionSampleSets(submissionId);
  hydrateSampleSetList(sampleSets);
  return sampleSets;
}

async function loadActiveSampleSet(sampleSetId: string | null) {
  if (!sampleSetId) {
    hydrateActiveSampleSet(null);
    return null;
  }

  const sampleSet = await api.getSampleSet(sampleSetId);
  hydrateActiveSampleSet(sampleSet);
  return sampleSet;
}

async function createSampleSet(submissionId: string, name: string): Promise<SubmissionSampleSet> {
  const sampleSet = await api.createSubmissionSampleSet(submissionId, {
    name,
    templates: [],
    multi_omics_form: clone(multiOmicsFormDefault),
    sample_environment_form: clone(sampleEnvironmentFormDefault),
    sender_shipping_info_form: clone(senderShippingInfoFormDefault),
    sample_data: clone(sampleDataDefault),
  });
  await loadSubmissionSampleSets(submissionId);
  hydrateActiveSampleSet(sampleSet);
  hasChanged.value = 0;
  return sampleSet;
}

watch(templateList, (newList, oldList) => {
  if (hasChanged.value === 0) {
    // Initial load, do nothing
    return;
  }
  if (isEqual(newList, oldList)) {
    return;
  }
  if (sampleEnvironmentForm.packageName.length === 0) {
    // If no package is selected, set the sample metadata validation to an untouched state
    sampleData.validation = null;
    return;
  }
  const newTabsValidated = {} as Record<string, boolean>;
  forEach(templateList.value, (templateKey) => {
    newTabsValidated[templateKey] = false;
  });
  if (sampleData.validation === null) {
    sampleData.validation = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  sampleData.validation.tabsValidated = newTabsValidated;

  // Remove sampleData and validation state for any templates that are no longer included in the package
  const removedTemplates = oldList.filter((template) => !newList.includes(template));
  if (removedTemplates.length > 0) {
    const newSampleData = { ...sampleData.data };
    removedTemplates.forEach((template) => {
      const sampleDataSlot = HARMONIZER_TEMPLATES[template as keyof typeof HARMONIZER_TEMPLATES]?.sampleDataSlot;
      if (sampleDataSlot === undefined) {
        return;
      }
      delete newSampleData[sampleDataSlot];
      if (sampleData.validation) {
        delete sampleData.validation.tabsValidated[template];
        delete sampleData.validation.invalidCells[template];
      }
    });
    sampleData.data = newSampleData;
  }
  hasChanged.value += 1;
});


function templateHasData(templateName: string = ''): boolean {
  //if DH hasn't been touched at all then there's no data nd it's ok edit
  if (Object.keys(sampleData.data).length === 0) {
    return false;
  }

  //case where we want behavior the same as 'templateChoiceDisabled'
  if (templateName === 'all') {
    const templateWithDataIndex = Object.values(sampleData.data).findIndex((value) => value.length > 0);
    if (templateWithDataIndex >= 0) {
      return true;
    }
    return false;
  }

  // If there are no keys in sampleData, the DH view hasn't been touched
  // yet, so it's still okay to change the template.
  // Or if the template is not present/hasn't been selected
  if (!Object.keys(sampleData.data).includes(templateName)) {
    return false;
  }
  // If the DH has been touched, see if the given template actually
  // contain data. If it does, then do not allow changing that template.
  // Otherwise, allow it to be changed.
  if (Object.values(sampleData.data[templateName] || {}).length > 0) {
    return true;
  }
  return false;
}

function checkJGITemplates() {
  //checks to see if there is data present in any of the templates that are associated with JGI
  const fields = ['jgi_mg', 'jgi_mg_lr', 'jgi_mt', 'data_mg', 'data_mg_interleaved', 'data_mt', 'data_mt_interleaved'];
  let data_present: boolean = false;
  fields.forEach((val) => {
    const sampleSlot = HARMONIZER_TEMPLATES[val]?.sampleDataSlot;
    if (isString(sampleSlot) && templateHasData(sampleSlot)) {
      data_present = true;
    }
  });
  return data_present;
}

function getPermissions(): Record<string, SubmissionEditorRole> {
  const permissions: Record<string, SubmissionEditorRole> = {};
  studyForm.contributors.forEach((contributor) => {
    const { orcid, permissionLevel } = contributor;
    if (orcid && permissionLevel) {
      permissions[orcid] = permissionLevel as SubmissionEditorRole;
    }
  });
  // This should happen last to ensure the PI is an owner
  if (studyForm.piOrcid) {
    permissions[studyForm.piOrcid] = 'owner';
  }
  return permissions;
}

// TODO: this will be refactored later to be a sample submit function.
// async function submit(submissionId: string, nextStatus?: SubmissionStatusKey) {
//   const uneditableReason = getSubmissionUneditableReason('owner');
//   if (uneditableReason) {
//     throw new Error(`Unable to submit: ${ uneditableReason }`);
//   }
//
//   if (sampleSetsState.activeSampleSetId === null) {
//     throw new Error('Unable to submit: no active sample set');
//   }
//
//   await incrementalSaveSubmission(submissionId);
//
//   if (nextStatus) {
//     const sampleSet = await api.updateSubmissionSampleSetStatus(sampleSetsState.activeSampleSetId, {
//       status: nextStatus,
//     });
//     hydrateActiveSampleSet(sampleSet);
//     await loadSubmissionSampleSets(submissionId);
//   }
//
//   await refreshSubmission(submissionId);
// }

async function selectActiveSampleSet(sampleSetId: string | null) {
  await loadActiveSampleSet(sampleSetId);
  hasChanged.value = 0;
}

function reset() {
  resetStore();
}

const incrementalSaveSubmissionRequest = useRequest();
async function incrementalSaveSubmission(id: string): Promise<void> {
  // This function **only** saves submission information. It does **not** deal with sample sets.
  const needsSubmissionSave = !isEqual(submissionState.draft.studyForm, studyFormDefault);
  const minimumPermissionLevel: SubmissionEditorRole = needsSubmissionSave ? 'editor' : 'metadata_contributor';
  const uneditableReason = getSubmissionUneditableReason(minimumPermissionLevel);
  if (uneditableReason) {
    return;
  }

  let submissionPayload: SubmissionMetadataPatch | null = null;
  const canEditSubmissionContext = hasMinimumPermissionLevel(getCurrentPermissionLevel(), 'editor');

  if (isOwner()) {
    submissionPayload = {
      study_form: studyForm,
      permissions: getPermissions(),
    };
  } else if (canEditSubmissionContext) {
    submissionPayload = {
      study_form: studyForm,
    };
  } else {
    return;
  }

  if (hasChanged.value) {
    const response = await incrementalSaveSubmissionRequest.request(
      async () => api.updateSubmission(id, submissionPayload)
    );
    if (response) {
      await updateStateFromSubmission(response);
    }
    hasChanged.value = 0;
    return;
  }
  hasChanged.value = 0;
}

async function createSubmission(isTestSubmission: boolean, studyName: string, piEmail: string): Promise<SubmissionMetadata> {
  reset();
  const submission = await api.createSubmission({
    study_form: {
      ...studyFormDefault,
      studyName,
      piEmail,
    },
    source_client: 'submission_portal',
    is_test_submission: isTestSubmission,
  });
  await updateStateFromSubmission(submission);
  return submission;
}

async function refreshSubmission(submissionId: string): Promise<SubmissionMetadata> {
  const submission = await api.getSubmission(submissionId);
  await updateStateFromSubmission(submission);
  return submission;
}

async function updateStateFromSubmission(submission: SubmissionMetadata) {
  hydrateSubmission(submission);

  const sampleSets = await loadSubmissionSampleSets(submission.id);
  const nextActiveSampleSetId = sampleSetsState.activeSampleSetId && sampleSets.some((sampleSet) => sampleSet.id === sampleSetsState.activeSampleSetId)
    ? sampleSetsState.activeSampleSetId
    : sampleSets[0]?.id ?? null;
  await loadActiveSampleSet(nextActiveSampleSetId);
  hasChanged.value = 0;
}

async function lockSubmission(id: string) {
  try {
    const lockResponse = await api.lockSubmission(id);
    if (submissionState.submission) {
      submissionState.submission.locked_by = lockResponse.locked_by || null;
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response && error.response.status === 409) {
        // Another user has the lock
        if (submissionState.submission) {
          submissionState.submission.locked_by = error.response.data.locked_by || null;
        }
      }
    } else {
      // Something went wrong, and we don't know who has the lock
      if (submissionState.submission) {
        submissionState.submission.locked_by = null;
      }
    }
  }
}

async function unlockSubmission(id: string) {
  try {
    await api.unlockSubmission(id);
    if (submissionState.submission) {
      submissionState.submission.locked_by = null;
    }
  } catch {
    // Ignore errors when unlocking
  }
}

async function loadSubmission(id: string) {
  reset();
  await refreshSubmission(id);
}

watch([
  senderShippingInfoForm,
  studyForm,
  multiOmicsForm,
  sampleEnvironmentForm,
  sampleData,
], () => { hasChanged.value += 1; }, { deep: true });

function mergeSampleData(key: string | undefined, data: any[]) {
  if (!key) {
    return;
  }
  sampleData.data = {
    ...sampleData.data,
    [key]: data,
  };
}

const fetchSuggestionsFromSampleRowsRequest = useRequest();
/**
 * Get metadata suggestions from the server and add them to the list of pending suggestions. Then sync the pending
 * suggestions with local storage.
 *
 * @param submissionId
 * @param schemaClassName
 * @param requests
 * @param batchSize
 */
async function fetchSuggestionsFromSampleRows(submissionId: string, schemaClassName: string, requests: MetadataSuggestionRequest[], batchSize: number = 10) {
  return fetchSuggestionsFromSampleRowsRequest.request(async () => {
    const batches = chunk(requests, batchSize);
    for (let i = 0; i < batches.length; i += 1) {
      const batch = batches[i] || [];


      const suggestions = await api.getMetadataSuggestions(batch, suggestionType.value);

      // Drop all the existing suggestions for the rows in this batch
      batch.forEach((request) => {
        metadataSuggestions.value = metadataSuggestions.value.filter(
          (suggestion) => suggestion.row !== request.row,
        );
      });

      // Add the new suggestions to the list
      metadataSuggestions.value.push(...suggestions);
    }

    setPendingSuggestions(submissionId, schemaClassName, metadataSuggestions.value);
  });
}

const fetchSuggestionsFromStudyInfoRequest = useRequest();
/**
 * Get suggestions from the server based on study information. These suggestions are not tied to specific submission
 * schema classes, so this function needs to sort out which classes the target slot is part of and then sync the pending
 * suggestions with local storage. If there is an existing suggestion for the same slot, row and type as an incoming
 * suggestion, the existing suggestion will be replaced by the incoming one. The in-memory list of suggestions will also
 * be updated to trigger reactivity in the UI if the active schema class is the one being updated.
 */
async function fetchSuggestionsFromStudyInfo(submissionId: string, allSchemaClassNames: string[], activeSchemaClassName: string, harmonizerApi: HarmonizerApi) {
  return fetchSuggestionsFromStudyInfoRequest.request(async () => {
    const suggestions = await api.getMetadataSuggestionsFromStudyDetails(submissionId);
    for (const schemaClassName of allSchemaClassNames) {
      const suggestionsForClass = getPendingSuggestions(submissionId, schemaClassName);
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
      setPendingSuggestions(submissionId, schemaClassName, suggestionsForClass);
      if (schemaClassName === activeSchemaClassName) {
        // If the active schema class is the one we just updated, also update the in-memory list of suggestions to trigger reactivity
        metadataSuggestions.value = getPendingSuggestions(submissionId, schemaClassName);
      }
    }
  });
}

/**
 * Remove the given metadata suggestions from the list of pending suggestions. Then sync the pending suggestions with
 * local storage.
 *
 * @param submissionId
 * @param schemaClassName
 * @param suggestions
 */
function removeMetadataSuggestions(submissionId: string, schemaClassName: string, suggestions: MetadataSuggestion[]) {
  metadataSuggestions.value = metadataSuggestions.value.filter(
    (suggestion) => !suggestions.includes(suggestion),
  );

  setPendingSuggestions(submissionId, schemaClassName, metadataSuggestions.value);
}

export {
  permissionLevelHierarchy,
  /* state */
  submissionState,
  sampleSetsState,
  uiState,
  activeSampleSet,
  sampleSetList,
  activeSampleSetId,
  multiOmicsForm,
  addAwardDoi,
  removeAwardDoi,
  sampleData,
  senderShippingInfoForm,
  senderShippingInfoFormDefault,
  studyForm,
  sampleEnvironmentForm,
  templateList,
  hasChanged,
  author,
  status,
  statusDisplay,
  studyName,
  createdDate,
  modifiedDate,
  submissionLockedBy,
  loggedInUserHasLock,
  isTestSubmission,
  incrementalSaveSubmissionRequest,
  primaryStudyImageUrl,
  piImageUrl,
  metadataSuggestions,
  suggestionMode,
  suggestionType,
  SubmissionStatusEnum,
  submissionPages,
  fetchSuggestionsFromSampleRowsRequest,
  fetchSuggestionsFromStudyInfoRequest,
  /* functions */
  getSubmissionUneditableReason,
  incrementalSaveSubmission,
  createSubmission,
  createSampleSet,
  loadSubmission,
  refreshSubmission,
  loadSubmissionSampleSets,
  loadActiveSampleSet,
  selectActiveSampleSet,
  lockSubmission,
  unlockSubmission,
  // submit,
  mergeSampleData,
  isOwner,
  editableByStatus,
  fetchSuggestionsFromSampleRows,
  fetchSuggestionsFromStudyInfo,
  removeMetadataSuggestions,
  templateHasData,
  checkJGITemplates,
  setTabValidated,
  setTabInvalidCells,
  resetSampleMetadataValidation,
  isSubmissionValid,
};
