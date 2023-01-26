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
const templateList = computed(() => {
  const checkBoxes = multiOmicsForm.omicsProcessingTypes;
  const template = HARMONIZER_TEMPLATES[packageName.value];
  const list = getVariant(checkBoxes, template.default);
  return list;
});

/**
 * DataHarmonizer Step
 */
const sampleData = shallowRef({} as Record<string, any[]>);
const samplesValid = ref(false);
const templateChoiceDisabled = computed(() => Object.keys(sampleData.value).length > 0);

/** Submit page */
const payloadObject: Ref<api.MetadataSubmission> = computed(() => ({
  packageName: packageName.value,
  templates: templateList.value,
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
  studyFormValid.value = false;
  Object.assign(studyForm, studyFormDefault);
  multiOmicsFormValid.value = false;
  Object.assign(multiOmicsForm, multiOmicsFormDefault);
  Object.assign(multiOmicsAssociations, multiOmicsAssociationsDefault);
  packageName.value = 'soil';
  sampleData.value = {};
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

function mergeSampleData(template: string, data: any[]) {
  sampleData.value = {
    ...sampleData.value,
    [`${template}_data`]: data,
  };
}

export {
  /* state */
  multiOmicsForm,
  multiOmicsAssociations,
  multiOmicsFormValid,
  sampleData,
  samplesValid,
  studyForm,
  studyFormValid,
  submitPayload,
  packageName,
  templateList,
  templateChoiceDisabled,
  /* functions */
  incrementalSaveRecord,
  generateRecord,
  loadRecord,
  submit,
  mergeSampleData,
};
