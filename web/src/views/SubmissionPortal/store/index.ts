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
