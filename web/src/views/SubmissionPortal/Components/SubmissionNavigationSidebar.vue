<script setup lang="ts">
import { useSubmissionStore } from '../store';
import { computed } from 'vue';
import { SubmissionPage } from '@/views/SubmissionPortal/types.ts';
import SubmissionNavigationSidebarItem from './SubmissionNavigationSidebarItem.vue';

const store = useSubmissionStore();

type SubmissionNavigationSection = {
  key: string;
  title: string;
  pages: SubmissionPage[];
};

const sections = computed<SubmissionNavigationSection[]>(() => {
  const submissionPages: SubmissionPage[] = [
    {
      title: 'Submission Summary',
      link: { name: 'Submission Summary' },
      validationMessages: null,
    },
    {
      title: 'Study Information',
      link: { name: 'Study Form' },
      validationMessages: store.submission.record?.study_form.validation ?? null,
    },
  ];

  const sampleSetSections = (store.submission.record?.sample_sets ?? []).map((sampleSet) => ({
    key: sampleSet.id,
    title: sampleSet.name,
    pages: [
      {
        title: 'Multi-omics Data',
        link: {
          name: 'Multiomics Form',
          params: { sampleSetId: sampleSet.id },
        },
        validationMessages: sampleSet.navigation_validation.multi_omics_data,
      },
      {
        title: 'Sample Environment',
        link: {
          name: 'Sample Environment',
          params: { sampleSetId: sampleSet.id },
        },
        validationMessages: sampleSet.navigation_validation.sample_environment,
      },
      {
        title: 'Sample Metadata',
        link: {
          name: 'Submission Sample Editor',
          params: { sampleSetId: sampleSet.id },
        },
        validationMessages: sampleSet.navigation_validation.sample_metadata,
      },
    ],
  }));

  return [
    {
      key: 'submission',
      title: '',
      pages: submissionPages,
    },
    ...sampleSetSections,
  ];
});
</script>

<template>
  <v-navigation-drawer
    app
    permanent
    clipped
  >
    <v-list-item>
      <template #title>
        <BreadcrumbList
          class="pt-3"
          :items="[
            { text: 'Submission Portal Home', to: { name: 'Submission Home' } }
          ]"
        />
        <div class="study-name">
          <span v-if="store.studyName">{{ store.studyName }}</span>
          <span
            v-else
            class="text-disabled font-italic"
          >
            No study name
          </span>
        </div>
      </template>
    </v-list-item>

    <v-list
      dense
      nav
    >
      <template
        v-for="section in sections"
        :key="section.key"
      >
        <v-divider />
        <SubmissionNavigationSidebarItem
          v-if="section.title"
          :title="section.title"
          :validation-messages="null"
        />
        <SubmissionNavigationSidebarItem
          v-for="page in section.pages"
          :key="`${section.key}-${page.title}`"
          :title="page.title"
          :link="page.link"
          :validation-messages="page.validationMessages"
        />
      </template>
    </v-list>
  </v-navigation-drawer>
</template>

<style scoped>
.study-name {
  font-weight: 600;
  white-space: normal !important;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  overflow: hidden;
}
</style>
