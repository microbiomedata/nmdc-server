<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import AuthButton from '@/components/Presentation/AuthButton.vue';
import { setConditions, stateRefs } from '@/store/';

export default defineComponent({
  name: 'App',
  components: { AuthButton },
  setup() {
    return {
      setConditions,
      stateRefs,
    };
  },
});
</script>

<template>
  <v-app>
    <v-app-bar
      app
      color="white"
      clipped-left
      elevation="1"
    >
      <a
        style="height: 100%"
        @click="setConditions([])"
      >
        <img
          src="/NMDC_logo_long.jpg"
          height="100%"
          alt="Page home"
        >
      </a>
      <v-spacer />

      <v-btn
        depressed
        small
        href="https://nmdc-documentation.readthedocs.io/en/latest/tutorials/nav_data_portal.html"
        target="_blank"
        rel="noopener noreferrer"
        class="mx-2"
      >
        Video Tutorial
        <v-icon
          class="pl-2"
          small
        >
          mdi-open-in-new
        </v-icon>
      </v-btn>

      <v-btn
        depressed
        small
        href="https://the-nmdc-portal-user-guide.readthedocs.io/en/latest/"
        target="_blank"
        rel="noopener noreferrer"
        class="mx-2"
      >
        User Guide
        <v-icon
          class="pl-2"
          small
        >
          mdi-open-in-new
        </v-icon>
      </v-btn>

      <v-btn
        depressed
        small
        href="https://nmdc-documentation.readthedocs.io/en/latest/index.html"
        target="_blank"
        rel="noopener noreferrer"
        class="mx-2"
      >
        NMDC Docs
        <v-icon
          class="pl-2"
          small
        >
          mdi-open-in-new
        </v-icon>
      </v-btn>

      <v-btn
        depressed
        small
        href="https://microbiomedata.org/"
        target="_blank"
        rel="noopener noreferrer"
        class="mx-2"
      >
        NMDC Home
        <v-icon
          class="pl-2"
          small
        >
          mdi-open-in-new
        </v-icon>
      </v-btn>

      <v-divider vertical />

      <v-btn
        depressed
        small
        color="secondary"
        :to="{ name: 'Submission Home' }"
        class="mx-2"
      >
        Submission Portal
        <v-icon
          class="pl-2"
          small
        >
          mdi-form-select
        </v-icon>
      </v-btn>
      <AuthButton />
    </v-app-bar>
    <keep-alive>
      <router-view />
    </keep-alive>
  </v-app>
</template>
