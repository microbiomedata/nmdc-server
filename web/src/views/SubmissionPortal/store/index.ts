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
  SuggestionsMode,
  SuggestionType,
} from '@/views/SubmissionPortal/types';
import { getPendingSuggestions, setPendingSuggestions } from '@/store/localStorage';
import * as api from './api';
import useRequest from '@/use/useRequest.ts';
import HarmonizerApi from '@/views/SubmissionPortal/harmonizerApi.ts';

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
const sampleEnvironmentValidationState = ref<string[] | null>(null);
const sampleDataValidationState = ref<SampleMetadataValidationState | null>(null);

function setTabValidated(tabName: string, validated: boolean) {
  if (sampleDataValidationState.value === null) {
      sampleDataValidationState.value = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  if (!templateList.value.includes(tabName)) {
    return;
  }
  sampleDataValidationState.value.tabsValidated[tabName] = validated;
}

function setTabInvalidCells(tabName: string, invalidCells: Record<number, Record<number, string>>) {
  if (sampleDataValidationState.value === null) {
    sampleDataValidationState.value = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  if (!templateList.value.includes(tabName)) {
    return;
  }
  sampleDataValidationState.value.invalidCells[tabName] = invalidCells;
}

function resetSampleMetadataValidation() {
  if (sampleDataValidationState.value === null) {
    sampleDataValidationState.value = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  sampleDataValidationState.value.invalidCells = {};
  Object.keys(sampleDataValidationState.value.tabsValidated).forEach((tab) => {
    sampleDataValidationState.value!.tabsValidated[tab] = false;
  });
}

function isSubmissionValid() {
  // The required forms must be validated with no errors
  if (!isEqual(studyForm.validationState, [])) {
    return false;
  }
  if (!isEqual(multiOmicsForm.validationState, [])) {
    return false;
  }
  if (!isEqual(sampleEnvironmentValidationState.value, [])) {
    return false;
  }
  // The sender shipping info form is optional. If it has been validated, it must have no errors
  if (addressForm.validationState != null && !isEqual(addressForm.validationState, [])) {
    return false;
  }
  // The sample metadata must be validated with no errors
  if (sampleDataValidationState.value == null) {
    return false;
  }
  const tabsValidatedValues = Object.values(sampleDataValidationState.value.tabsValidated);
  if (tabsValidatedValues.length === 0) {
    return false;
  }
  if (tabsValidatedValues.some((validated) => !validated)) {
    return false;
  }
  if (Object.values(sampleDataValidationState.value.invalidCells).some((cells) => Object.keys(cells).length > 0)) {
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
    validationMessages: studyForm.validationState,
  },
  {
    title: 'Multi-omics Data',
    link: { name: 'Multiomics Form' },
    validationMessages: combineErrors(multiOmicsForm.validationState, addressForm.validationState),
  },
  {
    title: 'Sample Environment',
    link: { name: 'Sample Environment' },
    validationMessages: sampleEnvironmentValidationState.value,
  },
  {
    title: 'Sample Metadata',
    link: { name: 'Submission Sample Editor' },
    validationMessages: combineSampleMetadataErrors(sampleDataValidationState.value),
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
  validationState: null as null | string[],
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
  publicationDois: [] as Doi[] | null,
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
  validationState: null as null | string[],
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
export type OmicsProcessingType =
  // non-doe types
  'mg' | 'mt' | 'mp' | 'mb' | 'mb-gc' | 'nom' | 'nom-lc' | 'lipidome' |
  // doe facility associated types
  'lipidome-emsl' | 'mp-emsl' | 'mb-emsl' | 'nom-emsl' | 'mg-jgi' | 'mg-lr-jgi' | 'mt-jgi' | 'mb-jgi';
const multiOmicsFormDefault = {
  award: null as null | string,
  awardDois: [] as Doi[] | null,
  dataGenerated: null as null | boolean,
  doe: null as null | boolean,
  facilities: [] as string[],
  facilityGenerated: null as null | boolean,
  JGIStudyId: '',
  mgCompatible: null as null | boolean,
  mgInterleaved: null as null | boolean,
  mtCompatible: null as null | boolean,
  mtInterleaved: null as null | boolean,
  omicsProcessingTypes: [] as OmicsProcessingType[],
  otherAward: null as null | string,
  ship: null as null | boolean,
  studyNumber: '',
  unknownDoi: null as null | boolean,
  mpProtocols: null as null | Protocols,
  mbProtocols: null as null | Protocols,
  mbGcProtocols: null as null | Protocols,
  lipProtocols: null as null | Protocols,
  nomProtocols: null as null | Protocols,
  nomLcProtocols: null as null | Protocols,
  validationState: null as null | string[],
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
  if ((multiOmicsForm.facilities?.length < multiOmicsForm.awardDois.length && !multiOmicsForm.dataGenerated) || (multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated && multiOmicsForm.awardDois.length > 1) || (!multiOmicsForm.facilityGenerated && multiOmicsForm.dataGenerated)) {
    multiOmicsForm.awardDois.splice(i, 1);
  }
}

function checkDoiFormat(v: string): string | boolean {
  return /^(?:doi:)?10.\d{2,9}\/.*$/.test(v) || 'DOI must be in the format "10.xxxx/xxxxx"';
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
  // EMSL was removed
  if (!newValue.includes('EMSL') && prevValue.includes('EMSL')) {
    multiOmicsForm.studyNumber = '';
    multiOmicsForm.ship = null;
    multiOmicsForm.omicsProcessingTypes = multiOmicsForm.omicsProcessingTypes.filter(t => (
      t !== 'lipidome-emsl' && t !== 'mp-emsl' && t !== 'mb-emsl' && t !== 'nom-emsl'
    ));
  }
  // JGI was removed
  if (!newValue.includes('JGI') && prevValue.includes('JGI')) {
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
    addressForm.validationState = null;
  }
});

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
    sampleDataValidationState.value = null;
    return;
  }
  const newTabsValidated = {} as Record<string, boolean>;
  forEach(templateList.value, (templateKey) => {
    newTabsValidated[templateKey] = false;
  });
  if (sampleDataValidationState.value === null) {
    sampleDataValidationState.value = {
      invalidCells: {},
      tabsValidated: {},
    };
  }
  sampleDataValidationState.value.tabsValidated = newTabsValidated;

  // Remove sampleData and validation state for any templates that are no longer included in the package
  const removedTemplates = oldList.filter((template) => !newList.includes(template));
  if (removedTemplates.length > 0) {
    const newSampleData = { ...sampleData.value };
    removedTemplates.forEach((template) => {
      const sampleDataSlot = HARMONIZER_TEMPLATES[template as keyof typeof HARMONIZER_TEMPLATES]?.sampleDataSlot;
      if (sampleDataSlot === undefined) {
        return;
      }
      delete newSampleData[sampleDataSlot];
      if (sampleDataValidationState.value) {
        delete sampleDataValidationState.value.tabsValidated[template];
        delete sampleDataValidationState.value.invalidCells[template];
      }
    });
    sampleData.value = newSampleData;
  }
  hasChanged.value += 1;
});

// *** IMPORTANT ***
// If you add a new field here, check whether the list of fields in the `can_save_submission` function
// in `nmdc_server/api.py` also needs to be updated.
const payloadObject: Ref<MetadataSubmission> = computed(() => ({
  packageName: packageName.value,
  addressForm,
  templates: templateList.value,
  studyForm,
  multiOmicsForm,
  sampleData: sampleData.value,
  sampleEnvironmentValidationState: sampleEnvironmentValidationState.value,
  sampleDataValidationState: sampleDataValidationState.value,
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
  let record = await api.updateRecord(id, payloadObject.value);
  if (status) {
    record = await api.updateSubmissionStatus(id, status);
  }
  updateStateFromRecord(record);
}

function reset() {
  Object.assign(addressForm, addressFormDefault);
  Object.assign(addressForm, addressFormDefault);
  Object.assign(studyForm, studyFormDefault);
  Object.assign(multiOmicsForm, multiOmicsFormDefault);
  Object.assign(multiOmicsAssociations, multiOmicsAssociationsDefault);
  packageName.value = [];
  sampleData.value = {};
  status.value = 'InProgress';
  studyName.value = '';
  isTestSubmission.value = false;
  primaryStudyImageUrl.value = null;
  piImageUrl.value = null;
  sampleEnvironmentValidationState.value = null;
  sampleDataValidationState.value = null;
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
    if (response) {
      console.log(response);
      updateStateFromRecord(response);
    }
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
  sampleEnvironmentValidationState.value = record.metadata_submission.sampleEnvironmentValidationState;
  sampleDataValidationState.value = record.metadata_submission.sampleDataValidationState;
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
  fetchSuggestionsFromSampleRowsRequest,
  fetchSuggestionsFromStudyInfoRequest,
  sampleEnvironmentValidationState,
  sampleDataValidationState,
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
  fetchSuggestionsFromSampleRows,
  fetchSuggestionsFromStudyInfo,
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
