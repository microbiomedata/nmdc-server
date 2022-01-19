import Vue from 'vue';
import CompositionApi, { reactive, ref, shallowRef } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';

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
  linkOutWebpage: '',
  studyDate: null,
  description: '',
  notes: '',
});

/**
 * Multi-Omics Form Step
 */
const multiOmicsFormValid = ref(false);
const multiOmicsForm = reactive({
  datasetDoi: '',
  alternativeNames: [],
  studyNumber: '',
  GOLDStudyId: '',
  JGIStudyId: '',
  NCBIBioProjectName: '',
  NCBIBioProjectId: '',
  omicsProcessingTypes: [],
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
const sampleData = shallowRef([]);
const samplesValid = ref(false);

export {
  studyForm,
  studyFormValid,
  multiOmicsForm,
  multiOmicsAssociations,
  multiOmicsFormValid,
  templateName,
  sampleData,
  samplesValid,
};
