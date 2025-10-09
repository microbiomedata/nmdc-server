/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */

// Composables
import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  base: import.meta.env.BASE_URL,
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
              redirect: () => ({ name: 'Submission Home' }),
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
  scrollBehavior: () => ({ x: 0, y: 0 }),
  parseQuery,
  stringifyQuery,
});,
})

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
