import Vue from 'vue';
import CompositionApi, { reactive, ref } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';

// TODO: Remove in version 3;
Vue.use(CompositionApi);

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

const multiOmicsForm = reactive({
  datasetDoi: '',
  alternativeNames: [],
  studyNumber: '',
  GOLDStudyId: '',
  JGIStudyId: '',
  NCBIBioProjectName: '',
  NCBIBioProjectId: '',
  dataWasGenerated: false,
});

const templateName = ref('MAM NMDC Dev Template' as keyof typeof HARMONIZER_TEMPLATES);

export {
  multiOmicsForm,
  studyForm,
  templateName,
};
