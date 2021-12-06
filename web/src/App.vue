<script>
import Auth from '@/components/Presentation/Auth.vue';

export default {
  name: 'App',
  components: { Auth },
};
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
        href="https://data.microbiomedata.org/"
        target="_blank"
        rel="noopener noreferrer"
        style="height: 100%"
      >
        <img
          src="/NMDC_logo_long.jpg"
          height="100%"
        >
      </a>
      <v-spacer />
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
        href="https://github.com/microbiomedata/nmdc-schema"
        target="_blank"
        rel="noopener noreferrer"
        class="mx-2"
      >
        Data Schema
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
        href="https://microbiomedata.org/workflows/"
        target="_blank"
        rel="noopener noreferrer"
        class="mx-2"
      >
        Workflows
        <v-icon
          class="pl-2"
          small
        >
          mdi-open-in-new
        </v-icon>
      </v-btn>
      <auth />
    </v-app-bar>
    <keep-alive>
      <router-view />
    </keep-alive>
  </v-app>
</template>
