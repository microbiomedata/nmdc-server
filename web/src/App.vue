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
      <auth />
    </v-app-bar>
    <keep-alive>
      <router-view />
    </keep-alive>
  </v-app>
</template>
