// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
import Vue from 'vue';
import CompositionApi, {
  computed, reactive, Ref, ref, shallowRef, watch,
} from '@vue/composition-api';
import {
  chunk, clone, forEach, isString,
} from 'lodash';
import axios from 'axios';
import * as api from './api';
import { User } from '@/types';
import {
  HARMONIZER_TEMPLATES,
  MetadataSubmission,
  MetadataSuggestion,
  NmdcAddress,
  PermissionLevelValues,
  PermissionTitle,
  SubmissionStatusKey,
  SubmissionStatusTitle,
  SuggestionType,
  SuggestionsMode,
  MetadataSuggestionRequest,
  DATA_MG_INTERLEAVED,
  DATA_MG,
  DATA_MT_INTERLEAVED,
  DATA_MT,
  EMSL,
  JGI_MG,
  JGI_MG_LR,
  JGI_MT,
} from '@/views/SubmissionPortal/types';
import { setPendingSuggestions } from '@/store/localStorage';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

const permissionTitleToDbValueMap: Record<PermissionTitle, PermissionLevelValues> = {
  Viewer: 'viewer',
  'Metadata Contributor': 'metadata_contributor',
  Editor: 'editor',
};

const permissionLevelHierarchy: Record<PermissionLevelValues, number> = {
  owner: 4,
  editor: 3,
  metadata_contributor: 2,
  viewer: 1,
};

//use schema enum to define submission status
const submissionStatus: Record<SubmissionStatusKey, SubmissionStatusTitle> = Object.fromEntries(
  Object.entries(NmdcSchema.enums.SubmissionStatusEnum.permissible_values).map(([key, item]: [SubmissionStatusKey, SubmissionStatusTitle]) => [key, item.title]),
);

console.log(submissionStatus);

const isSubmissionStatus = (str: any): str is SubmissionStatusTitle => Object.values(submissionStatus).includes(str);

const status = ref(submissionStatus.InProgress);
const isTestSubmission = ref(false);

/**
 * Submission record locking information
 */
let _submissionLockedBy: User | null = null;
function getSubmissionLockedBy(): User | null {
  return _submissionLockedBy;
}

let _permissionLevel: PermissionLevelValues | null = null;
function getPermissionLevel(): PermissionLevelValues | null {
  return _permissionLevel;
}

function isOwner(): boolean {
  if (!_permissionLevel) return false;
  return permissionLevelHierarchy[_permissionLevel] === permissionLevelHierarchy.owner;
}

function canEditSubmissionMetadata(): boolean {
  if (!_permissionLevel) return false;
  return permissionLevelHierarchy[_permissionLevel] >= permissionLevelHierarchy.editor;
}

function canEditSampleMetadata(): boolean {
  if (!_permissionLevel) return false;
  return permissionLevelHierarchy[_permissionLevel] >= permissionLevelHierarchy.metadata_contributor;
}

const hasChanged = ref(0);

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
  expectedShippingDate: undefined as undefined | Date,
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
const addressFormValid = ref(false);

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
  fundingSources: [] as string[] | null,
  description: '',
  notes: '',
  contributors: [] as {
    name: string;
    orcid: string;
    roles: string[];
    permissionLevel: PermissionLevelValues | null;
  }[],
  alternativeNames: [] as string[],
  GOLDStudyId: '',
  NCBIBioProjectId: '',
};
const studyFormValid = ref(false);
const studyForm = reactive(clone(studyFormDefault));

/**
 * Multi-Omics Form Step
 */
const multiOmicsFormDefault = {
  award: undefined as undefined | string,
  awardDois: [] as string[] | null,
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
};
const multiOmicsFormValid = ref(false);
const multiOmicsForm = reactive(clone(multiOmicsFormDefault));
const multiOmicsAssociationsDefault = {
  emsl: false,
  jgi: false,
  doi: false,
};
const multiOmicsAssociations = reactive(clone(multiOmicsAssociationsDefault));

function addAwardDoi() {
  if (multiOmicsForm.awardDois === null || multiOmicsForm.awardDois.length === 0) {
    multiOmicsForm.awardDois = [''];
  } else {
    multiOmicsForm.awardDois.push('');
  }
}

function removeAwardDoi(i: number) {
  if (multiOmicsForm.awardDois === null) {
    multiOmicsForm.awardDois = [''];
  }
  if ((multiOmicsForm.facilities.length < multiOmicsForm.awardDois.length && !multiOmicsForm.dataGenerated) || (multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated && multiOmicsForm.awardDois.length > 1) || (!multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated)) {
    multiOmicsForm.awardDois.splice(i, 1);
  }
}

/**
 * Environmental Package Step
 */
const packageName = ref([] as (keyof typeof HARMONIZER_TEMPLATES)[]);
const templateList = computed(() => {
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
    // eslint-disable-next-line no-lonely-if
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
  return Array.from(templates);
});
/**
 * DataHarmonizer Step
 */
const sampleData = shallowRef({} as Record<string, any[]>);
const metadataSuggestions = ref([] as MetadataSuggestion[]);
const suggestionMode = ref(SuggestionsMode.LIVE);
const suggestionType = ref(SuggestionType.ALL);

const tabsValidated = ref({} as Record<string, boolean>);
watch(templateList, () => {
  const newTabsValidated = {} as Record<string, boolean>;
  forEach(templateList.value, (templateKey) => {
    newTabsValidated[templateKey] = false;
  });
  tabsValidated.value = newTabsValidated;
});

/** Submit page */
const payloadObject: Ref<MetadataSubmission> = computed(() => ({
  packageName: packageName.value,
  addressForm,
  templates: templateList.value,
  studyForm,
  multiOmicsForm,
  sampleData: sampleData.value,
}));

function templateHasData(templateName: string): boolean {
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
  if (Object.values(sampleData.value[templateName]).length > 0) {
    return true;
  }
  return false;
}

function checkJGITemplates() {
  //checks to see if there is data present in any of the templates that are associated with JGI
  const fields = ['jgi_mg', 'jgi_mg_lr', 'jgi_mt', 'data_mg', 'data_mg_interleaved', 'data_mt', 'data_mt_interleaved'];
  let data_present: Boolean = false;
  fields.forEach((val) => {
    const sampleSlot = HARMONIZER_TEMPLATES[val].sampleDataSlot;
    if (isString(sampleSlot) && templateHasData(sampleSlot)) {
      data_present = true;
    }
  });
  return data_present;
}

function getPermissions(): Record<string, PermissionLevelValues> {
  const permissions: Record<string, PermissionLevelValues> = {};
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

function submit(id: string, status: SubmissionStatusTitle = submissionStatus.InProgress) {
  if (canEditSubmissionMetadata()) {
    return api.updateRecord(id, payloadObject.value, status);
  }
  throw new Error('Unable to submit due to inadequate permission level for this submission.');
}

function reset() {
  Object.assign(addressForm, addressFormDefault);
  addressFormValid.value = false;
  studyFormValid.value = false;
  addressFormValid.value = false;
  Object.assign(addressForm, addressFormDefault);
  Object.assign(studyForm, studyFormDefault);
  multiOmicsFormValid.value = false;
  Object.assign(multiOmicsForm, multiOmicsFormDefault);
  Object.assign(multiOmicsAssociations, multiOmicsAssociationsDefault);
  packageName.value = [];
  sampleData.value = {};
  status.value = submissionStatus.InProgress;
  isTestSubmission.value = false;
}

async function incrementalSaveRecord(id: string): Promise<number | void> {
  if (!canEditSampleMetadata()) {
    return Promise.resolve();
  }

  let payload: Partial<MetadataSubmission> = {};
  let permissions: Record<string, PermissionLevelValues> | undefined;
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
    const response = await api.updateRecord(id, payload, undefined, permissions);
    hasChanged.value = 0;
    return response.httpStatus;
  }
  hasChanged.value = 0;
  // Return a resolved Promise when hasChanged.value is false
  return Promise.resolve();
}

async function generateRecord(isTestSubBool: boolean) {
  reset();
  const record = await api.createRecord(payloadObject.value, isTestSubBool);
  isTestSubmission.value = isTestSubBool;
  return record;
}

async function loadRecord(id: string) {
  reset();
  const val = await api.getRecord(id);
  packageName.value = val.metadata_submission.packageName;
  Object.assign(studyForm, val.metadata_submission.studyForm);
  Object.assign(multiOmicsForm, val.metadata_submission.multiOmicsForm);
  Object.assign(addressForm, val.metadata_submission.addressForm);
  sampleData.value = val.metadata_submission.sampleData;
  hasChanged.value = 0;
  status.value = isSubmissionStatus(val.status) ? val.status : submissionStatus.InProgress;
  _permissionLevel = (val.permission_level as PermissionLevelValues);
  isTestSubmission.value = val.is_test_submission;

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
    const batch = batches[i];

    // eslint-disable-next-line no-await-in-loop -- we are intentionally throttling requests to the sever
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
  submissionStatus,
  permissionTitleToDbValueMap,
  permissionLevelHierarchy,
  /* state */
  multiOmicsForm,
  multiOmicsAssociations,
  multiOmicsFormValid,
  addAwardDoi,
  removeAwardDoi,
  sampleData,
  addressForm,
  addressFormDefault,
  addressFormValid,
  studyForm,
  studyFormValid,
  submitPayload,
  packageName,
  templateList,
  hasChanged,
  tabsValidated,
  status,
  isTestSubmission,
  metadataSuggestions,
  suggestionMode,
  suggestionType,
  /* functions */
  getSubmissionLockedBy,
  getPermissionLevel,
  incrementalSaveRecord,
  generateRecord,
  loadRecord,
  submit,
  mergeSampleData,
  isOwner,
  canEditSampleMetadata,
  canEditSubmissionMetadata,
  addMetadataSuggestions,
  removeMetadataSuggestions,
  templateHasData,
  checkJGITemplates,
};
