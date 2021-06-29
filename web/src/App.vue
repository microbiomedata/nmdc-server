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
        href="https://microbiomedata.org/"
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
        href="https://microbiomedata.org/metadata/"
        class="mx-2"
      >
        Metadata Standards
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
        class="mx-2"
      >
        Bioinformatics Workflows
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
