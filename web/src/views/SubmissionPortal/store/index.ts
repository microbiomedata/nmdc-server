import Vue from 'vue';
import CompositionApi, {
  computed, reactive, Ref, ref, shallowRef,
} from '@vue/composition-api';
import { clone } from 'lodash';
import * as api from './api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

const pastSubmissions: Ref<api.MetadataSubmissionRecord[]> = ref([]);
const activeSubmissionId: Ref<string> = ref('');

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
const templateName = ref('soil' as keyof typeof HARMONIZER_TEMPLATES);

/**
 * DataHarmonizer Step
 */
const sampleData = shallowRef([] as any[][]);
const samplesValid = ref(false);

/** Submit page */
const payloadObject: Ref<api.MetadataSubmission> = computed(() => ({
  template: templateName.value,
  studyForm,
  multiOmicsForm,
  sampleData: sampleData.value,
  status: 'complete',
}));

const submitPayload = computed(() => {
  const value = JSON.stringify(payloadObject.value, null, 2);
  return value;
});

async function populateList() {
  const val = await api.listRecords();
  pastSubmissions.value = val.results;
}

function submit() {
  return api.updateRecord(activeSubmissionId.value, payloadObject.value);
}

function reset() {
  studyFormValid.value = false;
  Object.assign(studyForm, studyFormDefault);
  multiOmicsFormValid.value = false;
  Object.assign(multiOmicsForm, multiOmicsFormDefault);
  Object.assign(multiOmicsAssociations, multiOmicsAssociationsDefault);
  templateName.value = 'soil';
  sampleData.value = [];
  samplesValid.value = false;
  activeSubmissionId.value = '';
}

async function incrementalSaveRecord() {
  const val: api.MetadataSubmission = {
    ...payloadObject.value,
    status: 'in progress',
  };
  if (activeSubmissionId.value) {
    const record = await api.updateRecord(activeSubmissionId.value, val);
    return record;
  }
  reset();
  const record = await api.createRecord(val);
  activeSubmissionId.value = record.id;
  return record;
}

async function loadRecord(id: string) {
  if (id !== activeSubmissionId.value) {
    reset();
    const val = await api.getRecord(id);
    templateName.value = val.metadata_submission.template;
    Object.assign(studyForm, val.metadata_submission.studyForm);
    Object.assign(multiOmicsForm, val.metadata_submission.multiOmicsForm);
    sampleData.value = val.metadata_submission.sampleData;
    activeSubmissionId.value = val.id;
  }
}

export {
  /* state */
  activeSubmissionId,
  multiOmicsForm,
  multiOmicsAssociations,
  multiOmicsFormValid,
  pastSubmissions,
  sampleData,
  samplesValid,
  studyForm,
  studyFormValid,
  submitPayload,
  templateName,
  /* functions */
  incrementalSaveRecord,
  loadRecord,
  populateList,
  submit,
};
