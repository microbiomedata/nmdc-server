<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({});
</script>

<template>
  <v-menu
    open-on-hover
    location="bottom start"
    :close-delay="200"
  >
    <template #activator="{ props }">
      <v-btn
        icon
        v-bind="props"
      >
        <v-icon>
          mdi-help-circle
        </v-icon>
      </v-btn>
    </template>

    <v-list>
      <v-list-item
        href="https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/portal_guide.html"
      >
        <v-list-item-title>User Guide</v-list-item-title>
      </v-list-item>
      <v-list-item
        href="https://nmdc-documentation.readthedocs.io/en/latest/index.html"
      >
        <v-list-item-title>NMDC Docs</v-list-item-title>
      </v-list-item>
      <v-list-item
        href="https://nmdc-documentation.readthedocs.io/en/latest/tutorials/nav_data_portal.html"
      >
        <v-list-item-title>Video Tutorial</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>
