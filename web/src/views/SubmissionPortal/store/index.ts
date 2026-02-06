import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';
import { computed, reactive, Ref, ref, shallowRef, watch, } from 'vue';
import { chunk, clone, forEach, isEqual, isString, } from 'lodash';
import axios from 'axios';
import { User } from '@/types';
import {
  AcquisitionProtocol,
  AllowedStatusTransitions,
  DATA_MG,
  DATA_MG_INTERLEAVED,
  DATA_MT,
  DATA_MT_INTERLEAVED,
  DataProtocol,
  Doi,
  EMSL,
  HARMONIZER_TEMPLATES,
  JGI_MG,
  JGI_MG_LR,
  JGI_MT,
  MetadataSubmission,
  MetadataSubmissionRecord,
  MetadataSuggestion,
  MetadataSuggestionRequest,
  NmdcAddress,
  PermissionTitle,
  SampleMetadataValidationState,
  SampleProtocol,
  SubmissionEditorRole,
  SubmissionPage,
  SubmissionStatusKey,
  SubmissionValidationState,
  SuggestionsMode,
  SuggestionType,
} from '@/views/SubmissionPortal/types';
import { setPendingSuggestions } from '@/store/localStorage';
import * as api from './api';
import useRequest from '@/use/useRequest.ts';

const permissionTitleToDbValueMap: Record<PermissionTitle, SubmissionEditorRole> = {
  Viewer: 'viewer',
  'Metadata Contributor': 'metadata_contributor',
  Editor: 'editor',
};

const permissionLevelHierarchy: Record<SubmissionEditorRole, number> = {
  owner: 4,
  editor: 3,
  metadata_contributor: 2,
  reviewer: 1,
  viewer: 1,
};

//use schema enum to define submission status
const SubmissionStatusEnum = NmdcSchema.enums.SubmissionStatusEnum.permissible_values; //enum from schema
const status = ref<SubmissionStatusKey>('InProgress');
const statusDisplay = computed(() => SubmissionStatusEnum[status.value].title);

function formatStatusTransitions(currentStatus: SubmissionStatusKey, dropdownType: SubmissionEditorRole | 'admin', transitions: AllowedStatusTransitions) {
  const excludeFromAll: SubmissionStatusKey[] = [
    'InProgress',
    'SubmittedPendingReview',
  ];

  // Admins can see all statuses and select any that aren't user invoked
  if (dropdownType === 'admin') {
    return (Object.keys(SubmissionStatusEnum) as SubmissionStatusKey[])
      .filter((key) => !excludeFromAll.includes(key) || key === currentStatus)
      .map((key) => ({
        value: key,
        title: SubmissionStatusEnum[key].title,
      }));
  }

  // Non-admins can only see and select allowed transitions
  const user_transitions = transitions[dropdownType] || {};
  const allowedStatusTransitions = user_transitions[currentStatus] || [];

  // Include the current status so it can be displayed
  const statusesToShow = [...allowedStatusTransitions];
  if (!statusesToShow.includes(currentStatus)) {
    statusesToShow.push(currentStatus);
  }

  // Return allowed transitions
  return (Object.keys(SubmissionStatusEnum) as SubmissionStatusKey[])
    .filter((key) => statusesToShow.includes(key as SubmissionStatusKey))
    .map((key) => ({
      value: key,
      title: SubmissionStatusEnum[key].title,
    }));
}

const studyName = ref('');
const createdDate = ref<Date | null>(null);
const modifiedDate = ref<Date | null>(null);
const isTestSubmission = ref(false);
const primaryStudyImageUrl = ref<string | null>(null);
const piImageUrl = ref<string | null>(null);
const author = ref<User | null>(null);

/**
 * Submission record locking information
 */
let _submissionLockedBy: User | null = null;
function getSubmissionLockedBy(): User | null {
  return _submissionLockedBy;
}

let _permissionLevel: SubmissionEditorRole | null = null;
function getPermissionLevel(): SubmissionEditorRole | null {
  return _permissionLevel;
}

function isOwner(): boolean {
  if (!_permissionLevel) return false;
  return permissionLevelHierarchy[_permissionLevel] === permissionLevelHierarchy.owner;
}

function editableByStatus(status: SubmissionStatusKey): boolean {
  const editableStatuses: SubmissionStatusKey[] = ['InProgress', 'UpdatesRequired'];
  return editableStatuses.includes(status);
}

function canEditSubmissionByStatus(): boolean {
  return editableByStatus(status.value);
}

function canEditSubmissionMetadata(): boolean {
  if (!_permissionLevel) return false;
  if (!canEditSubmissionByStatus()) return false;
  return permissionLevelHierarchy[_permissionLevel] >= permissionLevelHierarchy.editor;
}

function canEditSampleMetadata(): boolean {
  if (!_permissionLevel) return false;
  if (!canEditSubmissionByStatus()) return false;
  return permissionLevelHierarchy[_permissionLevel] >= permissionLevelHierarchy.metadata_contributor;
}

const hasChanged = ref(0);

/**
 * Validating forms
*/

const validationStateDefault: SubmissionValidationState = {
  studyForm: null,
  multiOmicsForm: null,
  sampleEnvironmentForm: null,
  senderShippingInfoForm: null,
  sampleMetadata: null,
};
const validationState = reactive(clone(validationStateDefault));

function setTabValidated(tabName: string, validated: boolean) {
  if (validationState.sampleMetadata === null) {
    validationState.sampleMetadata = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  validationState.sampleMetadata.tabsValidated[tabName] = validated;
}

function setTabInvalidCells(tabName: string, invalidCells: Record<number, Record<number, string>>) {
  if (validationState.sampleMetadata === null) {
    validationState.sampleMetadata = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  validationState.sampleMetadata.invalidCells[tabName] = invalidCells;
}

function resetSampleMetadataValidation() {
  if (validationState.sampleMetadata === null) {
    validationState.sampleMetadata = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  validationState.sampleMetadata.invalidCells = {};
  Object.keys(validationState.sampleMetadata.tabsValidated).forEach((tab) => {
    validationState.sampleMetadata!.tabsValidated[tab] = false;
  });
}

function isSubmissionValid() {
  // The required forms must be validated with no errors
  if (!isEqual(validationState.studyForm, [])) {
    return false;
  }
  if (!isEqual(validationState.multiOmicsForm, [])) {
    return false;
  }
  if (!isEqual(validationState.sampleEnvironmentForm, [])) {
    return false;
  }
  // The sender shipping info form is optional. If it has been validated, it must have no errors
  if (validationState.senderShippingInfoForm != null && !isEqual(validationState.senderShippingInfoForm, [])) {
    return false;
  }
  // The sample metadata must be validated with no errors
  if (validationState.sampleMetadata == null) {
    return false;
  }
  const tabsValidatedValues = Object.values(validationState.sampleMetadata.tabsValidated);
  if (tabsValidatedValues.length === 0) {
    return false;
  }
  if (tabsValidatedValues.some((validated) => !validated)) {
    return false;
  }
  if (Object.values(validationState.sampleMetadata.invalidCells).some((cells) => Object.keys(cells).length > 0)) {
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
    validationMessages: validationState.studyForm,
  },
  {
    title: 'Multi-omics Data',
    link: { name: 'Multiomics Form' },
    validationMessages: combineErrors(validationState.multiOmicsForm, validationState.senderShippingInfoForm),
  },
  {
    title: 'Sample Environment',
    link: { name: 'Sample Environment' },
    validationMessages: validationState.sampleEnvironmentForm,
  },
  {
    title: 'Sample Metadata',
    link: { name: 'Submission Sample Editor' },
    validationMessages: combineSampleMetadataErrors(validationState.sampleMetadata),
  },
]));

const addressFormDefault = {
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
  } as NmdcAddress,
  expectedShippingDate: undefined as undefined | string,
  shippingConditions: '',
  // Sample info
  sample: '',
  description: '',
  experimentalGoals: '',
  randomization: '',
  usdaRegulated: undefined as undefined | boolean,
  permitNumber: '',
  biosafetyLevel: '',
  irbOrHipaa: undefined as undefined | boolean,
  comments: '',
};

const addressForm = reactive(clone(addressFormDefault));

/**
 * Study Form Step
 */
const studyFormDefault = {
  studyName: '',
  piName: '',
  piEmail: '',
  piOrcid: '',
  linkOutWebpage: [],
  studyDate: null,
  dataDois: [] as Doi[] | null,
  fundingSources: [] as string[] | null,
  description: '',
  notes: '',
  contributors: [] as {
    name: string;
    orcid: string;
    roles: string[];
    permissionLevel: SubmissionEditorRole | null;
  }[],
  alternativeNames: [] as string[],
  GOLDStudyId: '',
  NCBIBioProjectId: '',
};
const studyForm = reactive(clone(studyFormDefault));

interface Protocols {
  sampleProtocol: SampleProtocol,
  acquisitionProtocol: AcquisitionProtocol,
  dataProtocol: DataProtocol,
}

/**
 * Multi-Omics Form Step
 */
const multiOmicsFormDefault = {
  award: undefined as undefined | string,
  awardDois: [] as Doi[] | null,
  dataGenerated: undefined as undefined | boolean,
  doe: undefined as undefined | boolean,
  facilities: [] as string[],
  facilityGenerated: undefined as undefined | boolean,
  JGIStudyId: '',
  mgCompatible: undefined as undefined | boolean,
  mgInterleaved: undefined as undefined | boolean,
  mtCompatible: undefined as undefined | boolean,
  mtInterleaved: undefined as undefined | boolean,
  omicsProcessingTypes: [] as string[],
  otherAward: undefined as undefined | string,
  ship: undefined as undefined | boolean,
  studyNumber: '',
  unknownDoi: undefined as undefined | boolean,
  mpProtocols: undefined as undefined | Protocols,
  mbProtocols: undefined as undefined | Protocols,
  lipProtocols: undefined as undefined | Protocols,
  nomProtocols: undefined as undefined | Protocols,
};
const multiOmicsForm = reactive(clone(multiOmicsFormDefault));
const multiOmicsAssociationsDefault = {
  emsl: false,
  jgi: false,
  doi: false,
};
const multiOmicsAssociations = reactive(clone(multiOmicsAssociationsDefault));

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
  if ((multiOmicsForm.facilities.length < multiOmicsForm.awardDois.length && !multiOmicsForm.dataGenerated) || (multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated && multiOmicsForm.awardDois.length > 1) || (!multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated)) {
    multiOmicsForm.awardDois.splice(i, 1);
  }
}

function checkDoiFormat(v: string) {
  const valid = /^(?:doi:)?10.\d{2,9}\/.*$/.test(v);
  return valid;
}

/**
 * Environmental Package Step
 */
const packageName = ref([] as (keyof typeof HARMONIZER_TEMPLATES)[]);
const templateList = computed<string[]>((prevTemplates) => {
  const templates = new Set(packageName.value);
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
      if (multiOmicsForm.facilities.includes('EMSL')) {
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
      if (multiOmicsForm.facilities.includes('JGI')) {
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
const sampleData = shallowRef({} as Record<string, any[]>);
const metadataSuggestions = ref([] as MetadataSuggestion[]);
const suggestionMode = ref(SuggestionsMode.LIVE);
const suggestionType = ref(SuggestionType.ALL);

watch(templateList, (newList, oldList) => {
  if (hasChanged.value === 0) {
    // Initial load, do nothing
    return;
  }
  if (isEqual(newList, oldList)) {
    return;
  }
  if (packageName.value.length === 0) {
    // If no package is selected, set the sample metadata validation to an untouched state
    validationState.sampleMetadata = null;
    return;
  }
  const newTabsValidated = {} as Record<string, boolean>;
  forEach(templateList.value, (templateKey) => {
    newTabsValidated[templateKey] = false;
  });
  if (validationState.sampleMetadata === null) {
    validationState.sampleMetadata = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  validationState.sampleMetadata.tabsValidated = newTabsValidated;
});

/** Submit page */
const payloadObject: Ref<MetadataSubmission> = computed(() => ({
  packageName: packageName.value,
  addressForm,
  templates: templateList.value,
  studyForm,
  multiOmicsForm,
  sampleData: sampleData.value,
  validationState,
}));

function templateHasData(templateName: string = ''): boolean {
  //if DH hasn't been touched at all then there's no data nd it's ok edit
  if (Object.keys(sampleData.value).length === 0) {
    return false;
  }

  //case where we want behavior the same as 'templateChoiceDisabled'
  if (templateName === 'all') {
    const templateWithDataIndex = Object.values(sampleData.value).findIndex((value) => value.length > 0);
    if (templateWithDataIndex >= 0) {
      return true;
    }
    return false;
  }

  // If there are no keys in sampleData, the DH view hasn't been touched
  // yet, so it's still okay to change the template.
  // Or if the template is not present/hasn't been selected
  if (!Object.keys(sampleData.value).includes(templateName)) {
    return false;
  }
  // If the DH has been touched, see if the given template actually
  // contain data. If it does, then do not allow changing that template.
  // Otherwise, allow it to be changed.
  if (Object.values(sampleData.value[templateName] || {}).length > 0) {
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
      permissions[orcid] = permissionLevel;
    }
  });
  // This should happen last to ensure the PI is an owner
  if (studyForm.piOrcid) {
    permissions[studyForm.piOrcid] = 'owner';
  }
  return permissions;
}

const submitPayload = computed(() => {
  const value = JSON.stringify(payloadObject.value, null, 2);
  return value;
});

async function submit(id: string, status?: SubmissionStatusKey) {
  if (!canEditSubmissionMetadata()) {
    throw new Error('Unable to submit due to inadequate permission level for this submission.');
  }
  if (!canEditSubmissionByStatus()) {
    throw new Error('Unable to submit with current submission status.');
  }
  const response = await api.updateRecord(id, payloadObject.value);
  let record = response.data;
  if (status) {
    record = await api.updateSubmissionStatus(id, status);
  }
  updateStateFromRecord(record);
}

function reset() {
  Object.assign(addressForm, addressFormDefault);
  Object.assign(addressForm, addressFormDefault);
  Object.assign(studyForm, studyFormDefault);
  Object.assign(validationState, validationStateDefault);
  Object.assign(multiOmicsForm, multiOmicsFormDefault);
  Object.assign(multiOmicsAssociations, multiOmicsAssociationsDefault);
  packageName.value = [];
  sampleData.value = {};
  status.value = 'InProgress';
  studyName.value = '';
  isTestSubmission.value = false;
  primaryStudyImageUrl.value = null;
  piImageUrl.value = null;
}

const incrementalSaveRecordRequest = useRequest();
async function incrementalSaveRecord(id: string): Promise<void> {
  if (!canEditSampleMetadata()) {
    return;
  }
  if (!canEditSubmissionByStatus()) {
    return;
  }

  let payload: Partial<MetadataSubmission> = {};
  let permissions: Record<string, SubmissionEditorRole> | undefined;
  if (isOwner()) {
    payload = payloadObject.value;
    permissions = getPermissions();
  } else if (canEditSubmissionMetadata()) {
    payload = payloadObject.value;
  } else if (canEditSampleMetadata()) {
    payload = {
      sampleData: payloadObject.value.sampleData,
    };
  }

  if (hasChanged.value) {
    const response = await incrementalSaveRecordRequest.request(
      () => api.updateRecord(id, payload, permissions)
    );
    updateStateFromRecord(response.data);
    return;
  }
  hasChanged.value = 0;
}

async function generateRecord(isTestSubBool: boolean, studyNameStr: string = '', piEmailStr: string = ''): Promise<MetadataSubmissionRecord> {
  reset();
  studyForm.studyName = studyNameStr;
  studyForm.piEmail = piEmailStr;
  const record = await api.createRecord(payloadObject.value, isTestSubBool);
  updateStateFromRecord(record);
  return record;
}

function updateStateFromRecord(record: MetadataSubmissionRecord) {
  packageName.value = record.metadata_submission.packageName;
  if (!isEqual(studyForm, record.metadata_submission.studyForm)) {
    Object.assign(studyForm, record.metadata_submission.studyForm);
  }
  if (!isEqual(multiOmicsForm, record.metadata_submission.multiOmicsForm)) {
    Object.assign(multiOmicsForm, record.metadata_submission.multiOmicsForm);
  }
  if (!isEqual(addressForm, record.metadata_submission.addressForm)) {
    Object.assign(addressForm, record.metadata_submission.addressForm);
  }
  if (!isEqual(validationState, record.metadata_submission.validationState)) {
    Object.assign(validationState, record.metadata_submission.validationState);
  }
  createdDate.value = new Date(record.created + 'Z');
  modifiedDate.value = new Date(record.date_last_modified + 'Z');
  sampleData.value = record.metadata_submission.sampleData;
  status.value = record.status;
  if (record.permission_level !== null) {
    _permissionLevel = (record.permission_level as SubmissionEditorRole);
  }
  studyName.value = record.study_name;
  isTestSubmission.value = record.is_test_submission;
  primaryStudyImageUrl.value = record.primary_study_image_url;
  piImageUrl.value = record.pi_image_url;
  hasChanged.value = 0;
  author.value = record.author;
}

async function lockRecord(id: string) {
  try {
    const lockResponse = await api.lockSubmission(id);
    _submissionLockedBy = lockResponse.locked_by || null;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response && error.response.status === 409) {
        // Another user has the lock
        _submissionLockedBy = error.response.data.locked_by || null;
      }
    } else {
      // Something went wrong, and we don't know who has the lock
      _submissionLockedBy = null;
    }
  }
}

async function unlockRecord(id: string) {
  try {
    await api.unlockSubmission(id);
    _submissionLockedBy = null;
  } catch {
    // Ignore errors when unlocking
  }
}

async function loadRecord(id: string) {
  reset();
  const val = await api.getRecord(id);
  updateStateFromRecord(val);
}

watch(payloadObject, () => { hasChanged.value += 1; }, { deep: true });

function mergeSampleData(key: string | undefined, data: any[]) {
  if (!key) {
    return;
  }
  sampleData.value = {
    ...sampleData.value,
    [key]: data,
  };
}

/**
 * Get metadata suggestions from the server and add them to the list of pending suggestions. Then sync the pending
 * suggestions with local storage.
 *
 * @param submissionId
 * @param schemaClassName
 * @param requests
 * @param batchSize
 */
async function addMetadataSuggestions(submissionId: string, schemaClassName: string, requests: MetadataSuggestionRequest[], batchSize: number = 10) {
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
  permissionTitleToDbValueMap,
  permissionLevelHierarchy,
  /* state */
  multiOmicsForm,
  multiOmicsAssociations,
  addAwardDoi,
  removeAwardDoi,
  sampleData,
  addressForm,
  addressFormDefault,
  studyForm,
  validationState,
  submitPayload,
  packageName,
  templateList,
  hasChanged,
  author,
  status,
  statusDisplay,
  studyName,
  createdDate,
  modifiedDate,
  isTestSubmission,
  incrementalSaveRecordRequest,
  primaryStudyImageUrl,
  piImageUrl,
  metadataSuggestions,
  suggestionMode,
  suggestionType,
  SubmissionStatusEnum,
  submissionPages,
  /* functions */
  getSubmissionLockedBy,
  getPermissionLevel,
  incrementalSaveRecord,
  generateRecord,
  loadRecord,
  lockRecord,
  unlockRecord,
  submit,
  mergeSampleData,
  isOwner,
  canEditSampleMetadata,
  canEditSubmissionMetadata,
  canEditSubmissionByStatus,
  editableByStatus,
  addMetadataSuggestions,
  removeMetadataSuggestions,
  templateHasData,
  checkJGITemplates,
  checkDoiFormat,
  formatStatusTransitions,
  setTabValidated,
  setTabInvalidCells,
  resetSampleMetadataValidation,
  isSubmissionValid,
};
