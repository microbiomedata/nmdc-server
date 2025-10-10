/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */

import { createRouter, createWebHistory } from 'vue-router'
import Search from '@/views/Search/SearchLayout.vue';
import SamplePage from '@/views/IndividualResults/SamplePage.vue';
import StudyPage from '@/views/IndividualResults/StudyPage.vue';
import UserPage from '@/views/User/UserPage.vue';
import UserDetailPage from '@/views/User/UserDetailPage.vue';
import LoginPage from '@/views/Login/LoginPage.vue';

/* Submission portal */
import MultiOmicsDataForm from '@/views/SubmissionPortal/Components/MultiOmicsDataForm.vue';
import StepperView from '@/views/SubmissionPortal/StepperView.vue';
import StudyForm from '@/views/SubmissionPortal/Components/StudyForm.vue';
import SubmissionView from '@/views/SubmissionPortal/SubmissionView.vue';
import TemplateChooser from '@/views/SubmissionPortal/Components/TemplateChooser.vue';
import HarmonizerView from '@/views/SubmissionPortal/HarmonizerView.vue';
import ValidateSubmit from '@/views/SubmissionPortal/Components/ValidateSubmit.vue';
import SubmissionList from '@/views/SubmissionPortal/Components/SubmissionList.vue';

import { unlockSubmission } from '@/views/SubmissionPortal/store/api';
import { incrementalSaveRecord } from '@/views/SubmissionPortal/store';

import { parseQuery, stringifyQuery } from './utils';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
          props: true,
          children: [
            {
              name: 'Submission root',
              path: '',
              redirect: '/submission/home',
            },
            {
              name: 'Submission Home',
              path: 'home',
              component: SubmissionList,
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
              name: 'Sample Environment',
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
    {
      path: '/user',
      name: 'User',
      component: UserDetailPage,
    },
    {
      path: '/login',
      name: 'Login',
      component: LoginPage,
    },
  ],
  scrollBehavior: (to, from, savedPosition) => {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0, left: 0 };
    }
  },
  parseQuery,
  stringifyQuery,
});
router.beforeEach((to, from, next) => {
  if (from.fullPath.includes('submission') && !!(from.params as any).id) {
    // We are navigating away from a submission edit screen, so save the progress
    incrementalSaveRecord((from.params as any).id);
    if (to.fullPath.includes('submission') && !!(to.params as any).id && (to.params as any).id === (from.params as any).id) {
      // We are navigating to a submission edit screen for the same submission, no need to  unlock
      next();
      return;
    }
    unlockSubmission((from.params as any).id);
  }
  next();
});
// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (localStorage.getItem('vuetify:dynamic-reload')) {
      console.error('Dynamic import error, reloading page did not fix it', err)
    } else {
      console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})

export default router
