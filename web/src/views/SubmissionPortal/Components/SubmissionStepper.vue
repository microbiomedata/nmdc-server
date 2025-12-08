<script lang="ts">
import {
  computed,
  defineComponent,
} from 'vue';
import { validForms } from '../store';
import { useRouter } from 'vue-router';

export default defineComponent({
  setup(props, { root }) {
    const pages = computed(() => [
      {
        title: 'Study Form',
        pageName: 'Study Form',
        icon: validForms.studyFormValid ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Multiomics Form',
        pageName: 'Multiomics Form',
        icon: validForms.multiOmicsFormValid ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Sample Environment',
        pageName: 'Sample Environment',
        icon: validForms.templatesValid ? 'mdi-check' : 'mdi-close-circle',
      },
      {
        title: 'Data Harmonizer',
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
      router?.push({ name: newPage });
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
    <v-list-item>
      <v-list-item-content>
        <v-list-item-title class="text-h6">
          Pages
        </v-list-item-title>
        <v-list-item-subtitle>
          Click to go to
        </v-list-item-subtitle>
      </v-list-item-content>
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
        @click="gotoPage(item.pageName)"
      >
        <v-list-item-icon>
          <v-icon>{{ item.icon }}</v-icon>
        </v-list-item-icon>

        <v-list-item-content>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>
