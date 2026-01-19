<script lang="ts">
import {
  computed,
  defineComponent,
} from 'vue';
import { validForms } from '../store';
import { useRouter } from 'vue-router';

export default defineComponent({
  setup() {
    const pages = computed(() => [
      {
        title: 'Study Form',
        pageName: 'Study Form',
        icon: validForms.studyFormValid.length === 0 ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Multiomics Form',
        pageName: 'Multiomics Form',
        icon: validForms.multiOmicsFormValid.length === 0 ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Sample Environment',
        pageName: 'Sample Environment',
        icon: validForms.templatesValid ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Sample Metadata',
        pageName: 'Submission Sample Editor',
        icon: validForms.harmonizerValid ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Submission Summary',
        pageName: 'Submission Summary',
        icon: 'mdi-text-box-outline',
      },
    ]);
    const router = useRouter();

    function gotoPage(newPage: string) {
      router?.push({name: newPage});
    }

    return {
      gotoPage,
      pages,
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
        <div class="text-h6">
          Pages
        </div>
      </template>
    </v-list-item>

    <v-divider />

    <v-list
      dense
      nav
    >
      <v-list-item
        v-for="item in pages"
        :key="item.title"
        link
        :append-icon="item.icon"
        :title="item.title"
        @click="gotoPage(item.pageName)"
      />
    </v-list>
  </v-navigation-drawer>
</template>
