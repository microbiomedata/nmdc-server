import Vue from 'vue';
import VueRouter, { Route } from 'vue-router';

import Search from '@/views/Search/SearchLayout.vue';
import SamplePage from '@/views/IndividualResults/SamplePage.vue';
import StudyPage from '@/views/IndividualResults/StudyPage.vue';

/* Submission portal */
import MultiOmicsDataForm from '@/views/SubmissionPortal/Components/MultiOmicsDataForm.vue';
import StepperView from '@/views/SubmissionPortal/StepperView.vue';
import SubmissionContextForm from '@/views/SubmissionPortal/Components/SubmissionContextForm.vue';
import StudyForm from '@/views/SubmissionPortal/Components/StudyForm.vue';
import SubmissionView from '@/views/SubmissionPortal/SubmissionView.vue';
import TemplateChooser from '@/views/SubmissionPortal/Components/TemplateChooser.vue';
import HarmonizerView from '@/views/SubmissionPortal/HarmonizerView.vue';
import ValidateSubmit from '@/views/SubmissionPortal/Components/ValidateSubmit.vue';
import SubmissionList from '@/views/SubmissionPortal/Components/SubmissionList.vue';

import UserPage from '@/views/User/UserPage.vue';

import { unlockSubmission } from '@/views/SubmissionPortal/store/api';

import { parseQuery, stringifyQuery } from './utils';

Vue.use(VueRouter);

const router = new VueRouter({
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
      props: true,
      children: [
        {
          component: StepperView,
          path: '',
          children: [
            {
              name: 'Submission root',
              path: '',
              redirect: () => ({ name: 'Submission Home' }),
            },
            {
              name: 'Submission Home',
              path: 'home',
              component: SubmissionList,
            },
            {
              name: 'Submission Context',
              path: ':id/context',
              component: SubmissionContextForm,
            },
            {
              name: 'Study Form',
              path: ':id/study',
              component: StudyForm,
            },
            {
              name: 'Multiomics Form',
              path: ':id/multiomics',
              component: MultiOmicsDataForm,
            },
            {
              name: 'Environment Package',
              component: TemplateChooser,
              path: ':id/templates',
            },
            {
              name: 'Validate And Submit',
              component: ValidateSubmit,
              path: ':id/submit',
            },
          ],
        },
        {
          name: 'Submission Sample Editor',
          component: HarmonizerView,
          path: ':id/samples',
        },
      ],
    },
    {
      path: '/users',
      name: 'Users',
      component: UserPage,
    },
  ],
  parseQuery,
  stringifyQuery,
});
router.beforeEach((to: Route, from: Route, next: Function) => {
  if (from.fullPath.includes('submission') && !!from.params.id) {
    // We are navigating away from a submission edit screen
    if (to.fullPath.includes('submission') && !!to.params.id && to.params.id === from.params.id) {
      // We are navigating to a submission edit screen for the same submission, no need to  unlock
      next();
      return;
    }
    console.log('unlocking submission');
    unlockSubmission(from.params.id);
  }
  next();
});

export default router;
