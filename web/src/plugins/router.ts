import Vue from 'vue';
import VueRouter from 'vue-router';

import Search from '@/views/Search/SearchLayout.vue';
import SamplePage from '@/views/IndividualResults/SamplePage.vue';
import StudyPage from '@/views/IndividualResults/StudyPage.vue';

/* Submission portal */
import MultiOmicsDataForm from '@/views/SubmissionPortal/Components/MultiOmicsDataForm.vue';
import StepperView from '@/views/SubmissionPortal/StepperView.vue';
import StudyForm from '@/views/SubmissionPortal/Components/StudyForm.vue';
import SubmissionView from '@/views/SubmissionPortal/SubmissionView.vue';
import TemplateChooser from '@/views/SubmissionPortal/Components/TemplateChooser.vue';
import HarmonizerView from '@/views/SubmissionPortal/HarmonizerView.vue';
import ValidateSubmit from '@/views/SubmissionPortal/Components/ValidateSubmit.vue';

import { parseQuery, stringifyQuery } from './utils';

Vue.use(VueRouter);

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'Search',
      component: Search,
    },
    {
      path: '/details/sample/:id',
      name: 'Sample',
      component: SamplePage,
      props: true,
    },
    {
      path: '/details/study/:id',
      name: 'Study',
      component: StudyPage,
      props: true,
    },
    {
      path: '/submission',
      component: SubmissionView,
      children: [
        {
          component: StepperView,
          path: '',
          children: [
            {
              name: 'Study Form',
              path: 'study',
              component: StudyForm,
            },
            {
              name: 'Multiomics Form',
              path: 'multiomics',
              component: MultiOmicsDataForm,
            },
            {
              name: 'Environment Package',
              component: TemplateChooser,
              path: 'templates',
            },
            {
              name: 'Validate And Submit',
              component: ValidateSubmit,
              path: 'submit',
            },
          ],
        },
        {
          name: 'Submission Sample Editor',
          component: HarmonizerView,
          path: 'samples',
        },
      ],
    },
  ],
  parseQuery,
  stringifyQuery,
});
