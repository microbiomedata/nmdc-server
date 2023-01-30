import Vue from 'vue';
import CompositionApi, {
  computed, reactive, Ref, ref, shallowRef, watch,
} from '@vue/composition-api';
import { clone } from 'lodash';
import * as api from './api';
import { getVariant, HARMONIZER_TEMPLATES } from '../harmonizerApi';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

const hasChanged = ref(0);
/**
 * Submission Context Step
 */
const contextFormDefault = {
  dataGenerated: undefined as undefined | boolean,
  facilityGenerated: undefined as undefined | boolean,
  facilities: [] as string[],
  // TODO strongly define what this type should look like
  shippingInfo: {},
  award: undefined as undefined | string,
  otherAward: '',
};
const addressFormDefault = {
  // Shipper info
  shipperName: '',
  shipperEmail: '',
  shipperPhone: '',
  shipperAddress1: '',
  shipperAddress2: '',
  shipperCity: '',
  shipperState: '',
  shipperZip: '',
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
  irpOrHipaa: undefined as undefined | boolean,
  // IRB info
  irbNumber: '',
  irbName: '',
  irbEmail: '',
  irbPhone: '',
  irbAddress1: '',
  irbAddress2: '',
  irbCity: '',
  irbState: '',
  irbZip: '',
  // Additional comments
  comments: '',
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
  }[],
};
const studyFormValid = ref(false);
const studyForm = reactive(clone(studyFormDefault));

/**
 * Multi-Omics Form Step
 */
const multiOmicsFormDefault = {
  datasetDoi: '',
  alternativeNames: [] as string[],
  studyNumber: '',
  GOLDStudyId: '',
  JGIStudyId: '',
  NCBIBioProjectName: '',
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
const templateChoice = computed(() => {
  const checkBoxes = multiOmicsForm.omicsProcessingTypes;
  const template = HARMONIZER_TEMPLATES[packageName.value];
  const choice = getVariant(checkBoxes, template.variations, template.default);
  return choice;
});

/**
 * DataHarmonizer Step
 */
const sampleData = shallowRef([] as any[][]);
const samplesValid = ref(false);
// row 1 and 2 are headers
const templateChoiceDisabled = computed(() => sampleData.value.length >= 3);

/** Submit page */
const payloadObject: Ref<api.MetadataSubmission> = computed(() => ({
  packageName: packageName.value,
  template: templateChoice.value,
  contextForm,
  studyForm,
  multiOmicsForm,
  sampleData: sampleData.value,
}));

const submitPayload = computed(() => {
  const value = JSON.stringify(payloadObject.value, null, 2);
  return value;
});

function submit(id: string) {
  return api.updateRecord(id, payloadObject.value, 'complete');
}

function reset() {
  contextFormValid.value = false;
  studyFormValid.value = false;
  Object.assign(studyForm, studyFormDefault);
  multiOmicsFormValid.value = false;
  Object.assign(multiOmicsForm, multiOmicsFormDefault);
  Object.assign(multiOmicsAssociations, multiOmicsAssociationsDefault);
  packageName.value = 'soil';
  sampleData.value = [];
  samplesValid.value = false;
}

async function incrementalSaveRecord(id: string) {
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
  sampleData.value = val.metadata_submission.sampleData;
  hasChanged.value = 0;
}

watch(payloadObject, () => { hasChanged.value += 1; }, { deep: true });

export {
  /* state */
  multiOmicsForm,
  multiOmicsAssociations,
  multiOmicsFormValid,
  sampleData,
  samplesValid,
  contextForm,
  contextFormValid,
  addressForm,
  addressFormValid,
  studyForm,
  studyFormValid,
  submitPayload,
  packageName,
  templateChoice,
  templateChoiceDisabled,
  /* functions */
  incrementalSaveRecord,
  generateRecord,
  loadRecord,
  submit,
};
