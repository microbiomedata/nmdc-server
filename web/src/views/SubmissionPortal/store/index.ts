import Vue from 'vue';
import CompositionApi, {
  computed, reactive, Ref, ref, shallowRef, watch,
} from '@vue/composition-api';
import { clone, forEach } from 'lodash';
import * as api from './api';
import { getVariants, HARMONIZER_TEMPLATES } from '../harmonizerApi';
import { User } from '@/data/api';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

enum BiosafetyLevels {
  BSL1 = 'BSL1',
  BSL2 = 'BSL2'
}

enum AwardTypes {
  CSP = 'CSP',
  BERSS = 'BERSS',
  BRCS = 'BRCs',
  MONET = 'MONet',
  FICUS = 'FICUS'
}

type permissionTitle = 'Viewer' | 'Metadata Contributor' | 'Editor';
type permissionLevelValues = 'viewer' | 'metadata_contributor' | 'editor' | 'owner';
const permissionTitleToDbValueMap: Record<permissionTitle, permissionLevelValues> = {
  Viewer: 'viewer',
  'Metadata Contributor': 'metadata_contributor',
  Editor: 'editor',
};

const permissionLevelHierarchy: Record<permissionLevelValues, number> = {
  owner: 4,
  editor: 3,
  metadata_contributor: 2,
  viewer: 1,
};

type SubmissionStatus = 'In Progress' | 'Submitted- Pending Review' | 'Complete';
const submissionStatus: Record<string, SubmissionStatus> = {
  InProgress: 'In Progress',
  SubmittedPendingReview: 'Submitted- Pending Review',
  Complete: 'Complete',
};

const isSubmissionStatus = (str: any): str is SubmissionStatus => Object.values(submissionStatus).includes(str);

const status = ref(submissionStatus.InProgress);

/**
 * Submission record locking information
 */
let _submissionLockedBy: User | null = null;
function getSubmissionLockedBy(): User | null {
  return _submissionLockedBy;
}

let _permissionLevel: permissionLevelValues | null = null;
function getPermissionLevel(): permissionLevelValues | null {
  return _permissionLevel;
}

function canEditPermissions(): boolean {
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
/**
 * Submission Context Step
 */
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
  } as api.NmdcAddress,
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
const contextFormDefault = {
  dataGenerated: undefined as undefined | boolean,
  datasetDoi: '',
  facilityGenerated: undefined as undefined | boolean,
  facilities: [] as string[],
  award: undefined as undefined | string,
  otherAward: '',
};
const contextForm = reactive(clone(contextFormDefault));
const contextFormValid = ref(false);
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
  description: '',
  notes: '',
  contributors: [] as {
    name: string;
    orcid: string;
    roles: string[];
    permissionLevel: permissionTitle | null;
  }[],
};
const studyFormValid = ref(false);
const studyForm = reactive(clone(studyFormDefault));

/**
 * Multi-Omics Form Step
 */
const multiOmicsFormDefault = {
  alternativeNames: [] as string[],
  studyNumber: '',
  GOLDStudyId: '',
  JGIStudyId: '',
  NCBIBioProjectId: '',
  omicsProcessingTypes: [] as string[],
};
const multiOmicsFormValid = ref(false);
const multiOmicsForm = reactive(clone(multiOmicsFormDefault));
const multiOmicsAssociationsDefault = {
  emsl: false,
  jgi: false,
  doi: false,
};
const multiOmicsAssociations = reactive(clone(multiOmicsAssociationsDefault));

/**
 * Environment Package Step
 */
const packageName = ref('soil' as keyof typeof HARMONIZER_TEMPLATES);
const templateList = computed(() => {
  const checkBoxes = multiOmicsForm.omicsProcessingTypes;
  const list = getVariants(checkBoxes, contextForm.dataGenerated, packageName.value);
  return list;
});

/**
 * DataHarmonizer Step
 */
const sampleData = shallowRef({} as Record<string, any[]>);
const templateChoiceDisabled = computed(() => {
  // If there are no keys in sampleData, the DH view hasn't been touched
  // yet, so it's still okay to change the template.
  if (Object.keys(sampleData.value).length === 0) {
    return false;
  }
  // If the DH has been touched, see if any of the values (templates) actually
  // contain data. If at least one does, then do not allow changing the template.
  // Otherwise, allow template changes.
  const templateWithDataIndex = Object.values(sampleData.value).findIndex((value) => value.length > 0);
  if (templateWithDataIndex >= 0) {
    return true;
  }
  return false;
});

const tabsValidated = ref({} as Record<string, boolean>);
watch(templateList, () => {
  const newTabsValidated = {} as Record<string, boolean>;
  forEach(templateList.value, (templateKey) => {
    newTabsValidated[templateKey] = false;
  });
  tabsValidated.value = newTabsValidated;
});

/** Submit page */
const payloadObject: Ref<api.MetadataSubmission> = computed(() => ({
  packageName: packageName.value,
  contextForm,
  addressForm,
  templates: templateList.value,
  studyForm,
  multiOmicsForm,
  sampleData: sampleData.value,
}));

const submitPayload = computed(() => {
  const value = JSON.stringify(payloadObject.value, null, 2);
  return value;
});

function submit(id: string, status: SubmissionStatus = submissionStatus.InProgress) {
  if (canEditSubmissionMetadata()) {
    return api.updateRecord(id, payloadObject.value, status);
  }
  throw new Error('Unable to submit due to inadequate permission level for this submission.');
}

function reset() {
  Object.assign(contextForm, contextFormDefault);
  contextFormValid.value = false;
  Object.assign(addressForm, addressFormDefault);
  addressFormValid.value = false;
  studyFormValid.value = false;
  addressFormValid.value = false;
  Object.assign(contextForm, contextFormDefault);
  Object.assign(addressForm, addressFormDefault);
  Object.assign(studyForm, studyFormDefault);
  multiOmicsFormValid.value = false;
  Object.assign(multiOmicsForm, multiOmicsFormDefault);
  Object.assign(multiOmicsAssociations, multiOmicsAssociationsDefault);
  packageName.value = 'soil';
  sampleData.value = {};
  status.value = submissionStatus.InProgress;
}

async function incrementalSaveRecord(id: string) {
  if (!canEditSubmissionMetadata()) {
    return;
  }
  const val: api.MetadataSubmission = {
    ...payloadObject.value,
  };
  if (hasChanged.value) {
    await api.updateRecord(id, val);
  }
  hasChanged.value = 0;
}

async function generateRecord() {
  reset();
  const record = await api.createRecord(payloadObject.value);
  return record;
}

async function loadRecord(id: string) {
  reset();
  const val = await api.getRecord(id);
  packageName.value = val.metadata_submission.packageName;
  Object.assign(studyForm, val.metadata_submission.studyForm);
  Object.assign(multiOmicsForm, val.metadata_submission.multiOmicsForm);
  Object.assign(contextForm, val.metadata_submission.contextForm);
  Object.assign(addressForm, val.metadata_submission.addressForm);
  sampleData.value = val.metadata_submission.sampleData;
  hasChanged.value = 0;
  status.value = isSubmissionStatus(val.status) ? val.status : submissionStatus.InProgress;
  _submissionLockedBy = val.locked_by;
  _permissionLevel = (val.permission_level as permissionLevelValues);
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

export {
  SubmissionStatus,
  submissionStatus,
  BiosafetyLevels,
  AwardTypes,
  permissionTitle,
  permissionTitleToDbValueMap,
  permissionLevelValues,
  permissionLevelHierarchy,
  /* state */
  multiOmicsForm,
  multiOmicsAssociations,
  multiOmicsFormValid,
  sampleData,
  contextForm,
  contextFormValid,
  addressForm,
  addressFormDefault,
  addressFormValid,
  studyForm,
  studyFormValid,
  submitPayload,
  packageName,
  templateList,
  templateChoiceDisabled,
  hasChanged,
  tabsValidated,
  status,
  /* functions */
  getSubmissionLockedBy,
  getPermissionLevel,
  incrementalSaveRecord,
  generateRecord,
  loadRecord,
  submit,
  mergeSampleData,
  canEditPermissions,
  canEditSampleMetadata,
  canEditSubmissionMetadata,
};
