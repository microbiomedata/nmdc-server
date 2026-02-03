<script lang="ts">
import { defineComponent, } from 'vue';
import { studyName, submissionPages } from '../store';

export default defineComponent({
  setup() {
    return {
      submissionPages,
      studyName
    };
  },
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
        <div class="study-name">
          <span v-if="studyName">{{ studyName }}</span>
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
        :to="{ name: 'Submission Summary' }"
        link
        title="Submission Summary"
      />
      <v-list-item
        v-for="page in submissionPages"
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
            color="green"
          >
            mdi-check-circle-outline
          </v-icon>
        </template>
      </v-list-item>
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
