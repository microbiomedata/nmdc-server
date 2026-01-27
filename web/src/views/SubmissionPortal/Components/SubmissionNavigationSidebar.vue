<script lang="ts">
import {
  computed,
  defineComponent,
} from 'vue';
import { validForms, studyForm } from '../store';
import { useRouter } from 'vue-router';

export default defineComponent({
  setup() {
    const pages = computed(() => [
      {
        title: 'Submission Summary',
        pageName: 'summary',
      },
      {
        title: 'Study Form',
        pageName: 'study',
        icon: validForms.studyFormValid.length === 0 ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Multiomics Form',
        pageName: 'multiomics',
        icon: validForms.multiOmicsFormValid.length === 0 ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Sample Environment',
        pageName: 'templates',
        icon: validForms.templatesValid ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Sample Metadata',
        pageName: 'samples',
        icon: validForms.harmonizerValid ? 'mdi-check' : 'mdi-close-circle',
      },
    ]);
    const router = useRouter();

    function gotoPage(newPage: string) {
      router?.push({name: newPage});
    }

    return {
      gotoPage,
      pages,
      studyForm
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
    <v-list-item subtitle="Click to go to">
      <template #title>
        <div class="text-h6 text-wrap">
          {{ studyForm.studyName }}
        </div>
      </template>
    </v-list-item>

    <v-divider />

    <v-list
      dense
      nav
    >
      <v-list-item
        v-for="(item, i) in pages"
        :key="i"
        :to="item.pageName"
        link
      >
        <v-list-item-title class="pr-2 text-subtitle-1">
          {{ item.title }}
        </v-list-item-title>
        <template v-if="item.icon" #append>
          <v-icon>{{ item.icon }}</v-icon>
        </template>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>
