<script>
export default {
  name: 'App',
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
      <router-link
        to="/"
        style="height: 100%"
      >
        <img
          src="/NMDC_logo_long.jpg"
          height="100%"
        >
      </router-link>
    </v-app-bar>
    <keep-alive>
      <router-view />
    </keep-alive>
  </v-app>
</template>
