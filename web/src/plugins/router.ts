import Vue from 'vue';
import VueRouter from 'vue-router';

import Search from '@/views/Search/SearchLayout.vue';
import SamplePage from '@/views/IndividualResults/SamplePage.vue';
import StudyPage from '@/views/IndividualResults/StudyPage.vue';

/* Submission portal */
import SubmissionView from '@/views/SubmissionPortal/SubmissionView.vue';
import TemplateoptionsPage from '@/views/SubmissionPortal/TemplateOptionsPage.vue';
import DataHarmonizerPage from '@/views/SubmissionPortal/DataHarmonizerPage.vue';

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
          name: 'Submission Sample Editor',
          component: DataHarmonizerPage,
          path: 'samples/:templateName',
          props: true,
        },
        {
          name: 'Submission Template Options',
          component: TemplateoptionsPage,
          path: 'templates',
          props: true,
        },
      ],
    },
  ],
  parseQuery,
  stringifyQuery,
});
