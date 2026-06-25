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
import SubmissionList from '@/views/SubmissionPortal/Components/SubmissionList.vue';
import SubmissionSummary from '@/views/SubmissionPortal/Components/SubmissionSummary.vue';
import SubmissionCreationForm from '@/views/SubmissionPortal/Components/SubmissionCreationForm.vue';
import SampleSetCreationForm from '@/views/SubmissionPortal/Components/SampleSetCreationForm.vue';
import { useSubmissionStore } from '@/views/SubmissionPortal/store';

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
          name: 'Create Submission',
          path: 'create',
          component: SubmissionCreationForm,
        },
        {
          component: StepperView,
          path: '',
          props: true,
          children: [
            {
              name: 'Create Sample Set',
              path: ':id/sample_set_create',
              component: SampleSetCreationForm,
              meta: { requiresSubmissionLock: true },
            },
            {
              name: 'Submission Summary',
              path: ':id/summary',
              component: SubmissionSummary,
            },
            {
              name: 'Study Form',
              path: ':id/study',
              component: StudyForm,
              meta: { requiresSubmissionLock: true },
            },
            {
              name: 'Multiomics Form',
              path: ':id/sample_set/:sampleSetId/multiomics',
              component: MultiOmicsDataForm,
              meta: { requiresSubmissionLock: true },
            },
            {
              name: 'Sample Environment',
              component: TemplateChooser,
              path: ':id/sample_set/:sampleSetId/templates',
              meta: { requiresSubmissionLock: true },
            },
          ],
        },
        {
          name: 'Submission Sample Editor',
          component: HarmonizerView,
          path: ':id/sample_set/:sampleSetId/samples',
          props: true,
          meta: { requiresSubmissionLock: true },
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

function getRouteParamString(param: unknown): string | undefined {
  if (Array.isArray(param)) {
    return param[0];
  }
  return typeof param === 'string' ? param : undefined;
}

async function ensureSubmissionLoaded(submissionId: string, store: ReturnType<typeof useSubmissionStore>) {
  if (store.submission.record?.id === submissionId) {
    return true;
  }
  await store.loadSubmission(submissionId);
  return store.submission.record?.id === submissionId;
}

router.beforeEach(async (to, from) => {
  const store = useSubmissionStore();
  const fromSubmissionId = getRouteParamString(from.params.id);
  const toSubmissionId = getRouteParamString(to.params.id);

  try {
    if (from.meta.requiresSubmissionLock && fromSubmissionId) {
      // We are navigating away from a submission edit screen, so save the progress
      await store.saveFormEdits();
      if (!to.meta.requiresSubmissionLock || toSubmissionId !== fromSubmissionId) {
        // We are navigating to a screen that does not require this lock, so unlock
        if (store.submission.record?.id === fromSubmissionId) {
          await store.unlockSubmission(fromSubmissionId);
        }
      }
    }
    if (
      to.meta.requiresSubmissionLock
      && toSubmissionId
      && (!from.meta.requiresSubmissionLock || fromSubmissionId !== toSubmissionId)
    ) {
      // We are navigating to a submission edit screen, so lock the record
      const submissionLoaded = await ensureSubmissionLoaded(toSubmissionId, store);
      if (submissionLoaded) {
        await store.lockSubmission(toSubmissionId);
      } else {
        console.warn(`Unable to lock submission ${toSubmissionId} because it could not be loaded`);
      }
    }
  } catch (e) {
    // If an error occurs during locking/unlocking, log it but allow navigation
    console.error('Error during navigation guard:', e);
  }
  return true;
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
