<script setup lang="ts">
import { useSubmissionStore } from '../store';
import { computed } from 'vue';
import { SubmissionPage } from '@/views/SubmissionPortal/types.ts';

const store = useSubmissionStore();

const pages = computed<SubmissionPage[]>(() => {
  const pages: SubmissionPage[] = [
    {
      title: 'Submission Summary',
      link: { name: 'Submission Summary' },
      validationMessages: null,
    },
    {
      title: 'Study Information',
      link: { name: 'Study Form' },
      validationMessages: store.submission.forms.studyForm.validation,
    },
  ];
  return pages;
})
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

    <v-divider />

    <v-list
      dense
      nav
    >
      <v-list-item
        v-for="page in pages"
        :key="page.title"
        :to="page.link"
        link
        :title="page.title"
      >
        <template
          v-if="Array.isArray(page.validationMessages)"
          #append
        >
          <v-badge
            v-if="page.validationMessages?.length != 0"
            inline
            color="red"
            :content="page.validationMessages?.length"
            :title="page.validationMessages.join('\n')"
          />
          <v-icon
            v-else
            style="margin-right: 2px"
            color="green"
          >
            mdi-check-circle-outline
          </v-icon>
        </template>
      </v-list-item>

      <template
        v-for="sampleSet in store.submission.record?.sample_sets"
        :key="sampleSet.id"
      >
        <v-list-item
          :title="sampleSet.name"
        />
        <v-list-item
          link
          title="Mutli-omics Data"
          :to="{
            name: 'Multiomics Form',
            params: { sampleSetId: sampleSet.id }
          }"
        />
        <v-list-item
          link
          title="Sample Environment"
          :to="{
            name: 'Sample Environment',
            params: { sampleSetId: sampleSet.id }
          }"
        />
        <v-list-item
          link
          title="Sample Metadata"
          :to="{
            name: 'Submission Sample Editor',
            params: { sampleSetId: sampleSet.id }
          }"
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
