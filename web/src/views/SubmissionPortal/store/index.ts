import Vue from 'vue';
import axios from 'axios';
import CompositionApi, {
  computed, reactive, ref, shallowRef,
} from '@vue/composition-api';

import { HARMONIZER_TEMPLATES } from '../harmonizerApi';

const client = axios.create({
  baseURL: process.env.VUE_APP_BASE_URL || '/api',
});

// TODO: Remove in version 3;
Vue.use(CompositionApi);

/**
 * Study Form Step
 */
const studyFormValid = ref(false);
const studyForm = reactive({
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
});

/**
 * Multi-Omics Form Step
 */
const multiOmicsFormValid = ref(false);
const multiOmicsForm = reactive({
  datasetDoi: '',
  alternativeNames: [] as string[],
  studyNumber: '',
  GOLDStudyId: '',
  JGIStudyId: '',
  NCBIBioProjectName: '',
  NCBIBioProjectId: '',
  omicsProcessingTypes: [] as string[],
});
const multiOmicsAssociations = reactive({
  emsl: false,
  jgi: false,
  doi: false,
});

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
const payloadObject = computed(() => ({
  template: templateName.value,
  studyForm,
  multiOmicsForm,
  sampleData: sampleData.value,
}));
const submitPayload = computed(() => {
  const value = JSON.stringify(payloadObject.value, null, 2);
  return value;
});

async function submit() {
  client.post('metadata_submission', {
    metadata_submission: payloadObject.value,
  });
}

export {
  studyForm,
  studyFormValid,
  multiOmicsForm,
  multiOmicsAssociations,
  multiOmicsFormValid,
  templateName,
  sampleData,
  samplesValid,
  submitPayload,
  submit,
};
