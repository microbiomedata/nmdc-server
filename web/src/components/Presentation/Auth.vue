<script>
import { api } from '@/data/api';

export default {
  asyncComputed: {
    async me() {
      return api.me();
    },
  },
};
</script>

<template>
  <div>
    <template v-if="me">
      <v-btn
        text
        color="grey darken-2"
      >
        <v-icon left>
          mdi-account-circle
        </v-icon>
        {{ me }}
      </v-btn>
      <v-btn
        icon
        color="grey darken-2"
        href="/logout"
      >
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </template>
    <template v-else>
      <v-btn
        text
        color="grey darken-2"
        href="/login"
      >
        <img
          width="28px"
          class="mr-2"
          src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
        >
        OrcID Login
      </v-btn>
    </template>
  </div>
</template>
